from datetime import datetime
import inspect
import logging

from PyPDF4.pdf import PdfFileReader
from asn1crypto import cms
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.db.models.fields.files import FileField
from django.db.models.signals import post_delete, post_save, \
    post_migrate, pre_save
from django.db.utils import DEFAULT_DB_ALIAS
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from sapl.base.email_utils import do_envia_email_tramitacao
from sapl.base.models import AuditLog, TipoAutor, Autor, Metadata
from sapl.decorators import receiver_multi_senders
from sapl.materia.models import Tramitacao
from sapl.parlamentares.models import Parlamentar
from sapl.protocoloadm.models import TramitacaoAdministrativo
from sapl.utils import get_base_url, models_with_gr_for_model


models_with_gr_for_autor = models_with_gr_for_model(Autor)


@receiver_multi_senders(post_save, senders=models_with_gr_for_autor)
def handle_update_autor_related(sender, **kwargs):
    # for m in models_with_gr_for_autor:
    instance = kwargs.get('instance')
    autor = instance.autor.first()
    if autor:
        autor.nome = str(instance)
        autor.save()


@receiver(post_save, sender=Tramitacao)
@receiver(post_save, sender=TramitacaoAdministrativo)
def handle_tramitacao_signal(sender, **kwargs):
    logger = logging.getLogger(__name__)

    tramitacao = kwargs.get('instance')

    if isinstance(tramitacao, Tramitacao):
        tipo = "materia"
        doc_mat = tramitacao.materia
    else:
        tipo = "documento"
        doc_mat = tramitacao.documento

    pilha_de_execucao = inspect.stack()
    for i in pilha_de_execucao:
        if i.function == 'migrate':
            return
        request = i.frame.f_locals.get('request', None)
        if request:
            break

    if not request:
        logger.warning("Email não enviado, objeto request é None.")
        return
    try:
        do_envia_email_tramitacao(
            get_base_url(request),
            tipo,
            doc_mat,
            tramitacao.status,
            tramitacao.unidade_tramitacao_destino)
    except Exception as e:
        logger.error(f'user={request.user.username}. Tramitação criada, mas e-mail de acompanhamento '
                     'de matéria não enviado. Há problemas na configuração '
                     'do e-mail. ' + str(e))


@receiver(post_delete)
def status_tramitacao_materia(sender, instance, **kwargs):
    if sender == Tramitacao:
        if instance.status.indicador == 'F':
            materia = instance.materia
            materia.em_tramitacao = True
            materia.save()
    elif sender == TramitacaoAdministrativo:
        if instance.status.indicador == 'F':
            documento = instance.documento
            documento.tramitacao = True
            documento.save()


def audit_log_function(sender, **kwargs):
    try:
        if not (sender._meta.app_config.name.startswith('sapl') or
                sender._meta.label == settings.AUTH_USER_MODEL):
            return
    except:
        # não é necessário usar logger, aqui é usada apenas para
        # eliminar um o if complexo
        return

    instance = kwargs.get('instance')
    if instance._meta.model == AuditLog:
        return

    logger = logging.getLogger(__name__)

    u = None
    pilha_de_execucao = inspect.stack()
    for i in pilha_de_execucao:
        if i.function == 'migrate':
            return
        r = i.frame.f_locals.get('request', None)
        try:
            if r.user._meta.label == settings.AUTH_USER_MODEL:
                u = r.user
                break
        except:
            # não é necessário usar logger, aqui é usada apenas para
            # eliminar um o if complexo
            pass

    try:
        operation = kwargs.get('operation')
        user = u
        model_name = instance.__class__.__name__
        app_name = instance._meta.app_label
        object_id = instance.id
        try:
            import json
            # [1:-1] below removes the surrounding square brackets
            str_data = serializers.serialize('json', [instance])[1:-1]
            data = json.loads(str_data)
        except:
            # old version capped string at AuditLog.MAX_DATA_LENGTH
            # so there can be invalid json fields in Prod.
            data = None

        if user:
            username = user.username
        else:
            username = ''

        AuditLog.objects.create(username=username,
                                operation=operation,
                                model_name=model_name,
                                app_name=app_name,
                                timestamp=timezone.now(),
                                object_id=object_id,
                                object='',
                                data=data)
    except Exception as e:
        logger.error('Error saving auditing log object')
        logger.error(e)


@receiver(post_delete)
def audit_log_post_delete(sender, **kwargs):
    audit_log_function(sender, operation='D', **kwargs)


@receiver(post_save)
def audit_log_post_save(sender, **kwargs):
    operation = 'C' if kwargs.get('created') else 'U'
    audit_log_function(sender, operation=operation, **kwargs)


def cria_models_tipo_autor(app_config=None, verbosity=2, interactive=True,
                           using=DEFAULT_DB_ALIAS, **kwargs):

    print("\n\033[93m\033[1m{}\033[0m".format(
        _('Atualizando registros TipoAutor do SAPL:')))
    for model in models_with_gr_for_autor:
        content_type = ContentType.objects.get_for_model(model)
        tipo_autor = TipoAutor.objects.filter(
            content_type=content_type.id).exists()

        if tipo_autor:
            msg1 = "Carga de {} não efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " Já Existe um {} {} relacionado...".format(
                TipoAutor._meta.verbose_name,
                model._meta.verbose_name)
            msg = "  {}{}".format(msg1, msg2)
        else:
            novo_autor = TipoAutor()
            novo_autor.content_type_id = content_type.id
            novo_autor.descricao = model._meta.verbose_name
            novo_autor.save()
            msg1 = "Carga de {} efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " {} {} criado...".format(
                TipoAutor._meta.verbose_name, content_type.model)
            msg = "  {}{}".format(msg1, msg2)
        print(msg)
    # Disconecta função para evitar a chamada repetidas vezes.
    post_migrate.disconnect(receiver=cria_models_tipo_autor)


post_migrate.connect(receiver=cria_models_tipo_autor)


def signed_files_extraction_function(sender, instance, **kwargs):

    def run_signed_name_and_date_via_fields(fields):
        signs = []

        for key, field in fields.items():

            if '/FT' not in field and field['/FT'] != '/Sig':
                continue
            if '/V' not in field:
                continue

            content_sign = field['/V']['/Contents']
            nome = 'Nome do assinante não localizado.'
            oname = ''
            try:
                info = cms.ContentInfo.load(content_sign)
                signed_data = info['content']
                oun_old = []
                for cert in signed_data['certificates']:
                    subject = cert.native['tbs_certificate']['subject']
                    issuer = cert.native['tbs_certificate']['issuer']
                    oname = issuer.get('organization_name', '')

                    if oname == 'Gov-Br':
                        nome = subject['common_name'].split(':')[0]
                        continue

                    oun = subject['organizational_unit_name']

                    if isinstance(oun, str):
                        continue

                    if len(oun) > len(oun_old):
                        oun_old = oun
                        nome = subject['common_name'].split(':')[0]

                    if oun and isinstance(oun, list) and len(oun) == 4:
                        oname += ' - ' + oun[3]
                        break

            except:
                if '/Name' in field['/V']:
                    nome = field['/V']['/Name']

            fd = None
            try:
                data = str(field['/V']['/M'])

                if 'D:' not in data:
                    data = None
                else:
                    if not data.endswith('Z'):
                        data = data.replace('Z', '+')
                    data = data.replace("'", '')

                    fd = datetime.strptime(data[2:], '%Y%m%d%H%M%S%z')
            except:
                pass

            signs.append((nome, [fd, oname]))

        return signs

    def run_signed_name_and_date_extract(file):
        signs = {}
        fields = {}
        pdfdata = file.read()

        # se não tem byterange então não é assinado
        byterange = []
        n = -1
        while True:
            n = pdfdata.find(b"/ByteRange", n + 1)
            if n == -1:
                break
            byterange.append(n)

        if not byterange:
            return signs

        # tenta extrair via /Fields
        try:
            pdf = PdfFileReader(file)
            fields = pdf.getFields()
        except Exception as e:
            try:
                pdf = PdfFileReader(file, strict=False)
                fields = pdf.getFields()
            except Exception as ee:
                fields = ee

        try:
            # se a extração via /Fields ocorrer sem erros e forem capturadas
            # tantas assinaturas quanto byteranges
            if isinstance(fields, dict):
                signs = run_signed_name_and_date_via_fields(fields)
                if len(signs) == len(byterange):
                    return signs

            for n in byterange:

                start = pdfdata.find(b"[", n)
                stop = pdfdata.find(b"]", start)
                assert n != -1 and start != -1 and stop != -1
                n += 1

                br = [int(i, 10) for i in pdfdata[start + 1: stop].split()]
                contents = pdfdata[br[0] + br[1] + 1: br[2] - 1]
                bcontents = bytes.fromhex(contents.decode("utf8"))
                data1 = pdfdata[br[0]: br[0] + br[1]]
                data2 = pdfdata[br[2]: br[2] + br[3]]
                #signedData = data1 + data2

                nome = 'Nome do assinante não localizado.'
                oname = ''
                try:
                    info = cms.ContentInfo.load(bcontents)
                    signed_data = info['content']

                    oun_old = []
                    for cert in signed_data['certificates']:
                        subject = cert.native['tbs_certificate']['subject']
                        issuer = cert.native['tbs_certificate']['issuer']
                        oname = issuer.get('organization_name', '')

                        if oname == 'Gov-Br':
                            nome = subject['common_name'].split(':')[0]
                            continue

                        oun = subject['organizational_unit_name']

                        if isinstance(oun, str):
                            continue

                        if len(oun) > len(oun_old):
                            oun_old = oun
                            nome = subject['common_name'].split(':')[0]

                        if oun and isinstance(oun, list) and len(oun) == 4:
                            oname += ' - ' + oun[3]
                            break

                except Exception as e:
                    pass

                fd = None
                signs.append((nome, [fd, oname]))

        except Exception as e:
            pass

        return signs

    def signed_name_and_date_extract(file):

        try:
            signs = run_signed_name_and_date_extract(file)
        except:
            return {}

        signs = sorted(signs, key=lambda sign: (
            sign[0], sign[1][1], sign[1][0]))

        signs_dict = {}

        for s in signs:
            if s[0] not in signs_dict or 'ICP' in s[1][1] and 'ICP' not in signs_dict[s[0]][1]:
                signs_dict[s[0]] = s[1]

        signs = sorted(signs_dict.items(), key=lambda sign: (
            sign[0], sign[1][1], sign[1][0]))

        sr = []

        for s in signs:
            tt = s[0].title().split(' ')
            for idx, t in enumerate(tt):
                if t in ('Dos', 'De', 'Da', 'Do', 'Das', 'E'):
                    tt[idx] = t.lower()
            sr.append((' '.join(tt), s[1]))

        signs = sr

        meta_signs = {
            'autores': [],
            'admin': []
        }

        for s in signs:
            # cn = # settings.CERT_PRIVATE_KEY_NAME
            #meta_signs['admin' if s[0] == cn else 'autores'].append(s)
            meta_signs['autores'].append(s)
        return meta_signs

    def filefield_from_model(m):
        fields = m._meta.get_fields()
        fields = tuple(map(lambda f: f.name, filter(
            lambda x: isinstance(x, FileField), fields)))
        return fields

    FIELDFILE_NAME = filefield_from_model(instance)

    if not FIELDFILE_NAME:
        return

    try:
        md = Metadata.objects.get(
            content_type=ContentType.objects.get_for_model(
                instance._meta.model),
            object_id=instance.id,).metadata
    except:
        md = {}

    for fn in FIELDFILE_NAME:  # fn -> field_name
        ff = getattr(instance, fn)  # ff -> file_field

        if md and 'signs' in md and \
                fn in md['signs'] and\
                md['signs'][fn]:
            md['signs'][fn] = {}

        if not ff:
            continue

        try:
            file = ff.file.file
            meta_signs = {}
            if not isinstance(ff.file, UploadedFile):
                absolute_path = ff.path
                with open(absolute_path, "rb") as file:
                    meta_signs = signed_name_and_date_extract(file)
                    file.close()
            else:
                file.seek(0)
                meta_signs = signed_name_and_date_extract(file)

            if not meta_signs or not meta_signs['autores'] and not meta_signs['admin']:
                continue

            if not md:
                md = {'signs': {}}

            if 'signs' not in md:
                md['signs'] = {}

            md['signs'][fn] = meta_signs
        except Exception as e:
            # print(e)
            pass

    if md:
        metadata = Metadata.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(
                instance._meta.model),
            object_id=instance.id,)
        metadata[0].metadata = md
        metadata[0].save()


@receiver(pre_save, dispatch_uid='signed_files_extraction_pre_save_signal')
def signed_files_extraction_pre_save_signal(sender, instance, **kwargs):

    signed_files_extraction_function(sender, instance, **kwargs)
