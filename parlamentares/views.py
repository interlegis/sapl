import os
from io import BytesIO
from re import sub

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms.fields import ImageField
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from vanilla import GenericView

from crud import build_crud

from .forms import (DependenteEditForm, DependenteForm, FiliacaoEditForm,
                    FiliacaoForm, MandatoEditForm, MandatoForm,
                    ParlamentaresEditForm, ParlamentaresForm,
                    ParlamentaresListForm)
from .models import (CargoMesa, Coligacao, ComposicaoMesa, Dependente,
                     Filiacao, Legislatura, Mandato, NivelInstrucao,
                     Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar,
                     TipoAfastamento, TipoDependente)

cargo_mesa_crud = build_crud(
    CargoMesa, 'cargo_mesa', [

        [_('Cargo na Mesa'),
         [('descricao', 10),
            ('unico', 2)]],
    ])

legislatura_crud = build_crud(
    Legislatura, 'tabelas_auxiliares#legislatura', [

        [_('Legislatura'),
         [('data_inicio', 4), ('data_fim', 4), ('data_eleicao', 4)]],
    ])

coligacao_crud = build_crud(
    Coligacao, 'coligacao', [

        [_('Coligação'),
         [('nome', 5),
            ('legislatura', 5),
            ('numero_votos', 2)]],
    ])

partido_crud = build_crud(
    Partido, 'partidos', [

        [_('Partido Político'),
         [('nome', 6),
            ('sigla', 2),
            ('data_criacao', 2),
            ('data_extincao', 2)]],
    ])


dependente_crud = build_crud(
    Dependente, '', [

        [_('Dependentes'),
         [('nome', 12)],
            [('tipo', 4), ('sexo', 4), ('data_nascimento', 4)],
            [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)]],
    ])


sessao_legislativa_crud = build_crud(
    SessaoLegislativa, 'sessao_legislativa', [

        [_('Sessão Legislativa'),
            [('numero', 4),
             ('tipo', 4),
             ('legislatura', 4),
             ('data_inicio', 6),
             ('data_fim', 6),
             ('data_inicio_intervalo', 6),
             ('data_fim_intervalo', 6)]],
    ])


parlamentar_crud = build_crud(
    Parlamentar, '', [

        [_('Cadastro do Parlamentar'),
         [('nome_parlamentar', 8), ('ativo', 4)],
            [('nome_completo', 12)],
            [('nivel_instrucao', 4), ('sexo', 4), ('data_nascimento', 4)],
            [('cpf', 4), ('rg', 4), ('titulo_eleitor', 4)],
            [('situacao_militar', 6), ('profissao', 6)],
            [('endereco_web', 12)],
            [('email', 12)],
            [('numero_gab_parlamentar', 4), ('telefone', 4), ('fax', 4)],
            [('endereco_residencia', 6), ('cep_residencia', 6)],
            [('municipio_residencia', 12)],
            [('telefone_residencia', 6), ('fax_residencia', 6)],
            [('locais_atuacao', 12)],
            [('fotografia', 12)],
            [('biografia', 12)]],
    ])

filiacao_crud = build_crud(
    Filiacao, '', [

        [_('Filiações Partidárias '),
         [('partido', 4), ('data', 4), ('data_desfiliacao', 4)]],
    ])

mandato_crud = build_crud(
    Mandato, '', [

        [_('Mandato'),
         [('legislatura', 4), ('coligacao', 4), ('votos_recebidos', 4)],
            [('ind_titular_FIXME', 3),
             ('dat_inicio_mandato_FIXME', 3),
             ('data_fim_mandato', 3),
             ('data_expedicao_diploma', 3)],
            [('observacao', 12)]],
    ])

tipo_dependente_crud = build_crud(
    TipoDependente, 'tipo_dependente', [

        [_('Tipo de Dependente'),
         [('descricao', 12)]],
    ])

nivel_instrucao_crud = build_crud(
    NivelInstrucao, 'nivel_instrucao', [

        [_('Nível Instrução'),
         [('descricao', 12)]],
    ])

tipo_afastamento_crud = build_crud(
    TipoAfastamento, 'tipo_afastamento', [

        [_('Tipo de Afastamento'),
         [('descricao', 5), ('dispositivo', 5), ('afastamento', 2)]],
    ])

tipo_militar_crud = build_crud(
    SituacaoMilitar, 'tipo_situa_militar', [

        [_('Tipo Situação Militar'),
         [('descricao', 12)]],
    ])


class ParlamentaresView(GenericView):
    template_name = "parlamentares/parlamentares_list.html"

    def get(self, request, *args, **kwargs):
        form = ParlamentaresListForm()

        if not Legislatura.objects.all():
            mensagem = "Cadastre alguma Legislatura antes\
            de cadastrar algum Parlamentar"
            messages.add_message(request, messages.INFO, mensagem)
            return self.render_to_response(
                {'legislaturas': [],
                 'legislatura_id': 0,
                 'form': form,
                 })

        legislaturas = Legislatura.objects.all().order_by(
            '-data_inicio', '-data_fim')

        mandatos = Mandato.objects.filter(
            legislatura_id=legislaturas.first().id)

        parlamentares = []
        dict_parlamentar = {}
        for m in mandatos:

            if m.parlamentar.filiacao_set.last():
                partido = m.parlamentar.filiacao_set.last().partido.sigla
            else:
                partido = 'Sem Registro'

            dict_parlamentar = {
                'id': m.parlamentar.id,
                'nome': m.parlamentar.nome_parlamentar,
                'partido': partido,
                'ativo': m.parlamentar.ativo}
            parlamentares.append(dict_parlamentar)

        return self.render_to_response(
            {'legislaturas': legislaturas,
             'legislatura_id': legislaturas.first().id,
             'form': form,
             'parlamentares': parlamentares})

    def post(self, request, *args, **kwargs):
        form = ParlamentaresListForm(request.POST)

        mandatos = Mandato.objects.filter(
            legislatura_id=int(form.data['periodo']))

        parlamentares = []
        dict_parlamentar = {}
        for m in mandatos:

            if m.parlamentar.filiacao_set.last():
                partido = m.parlamentar.filiacao_set.last().partido.sigla
            else:
                partido = 'Sem Registro'

            dict_parlamentar = {
                'id': m.parlamentar.id,
                'nome': m.parlamentar.nome_parlamentar,
                'partido': partido,
                'ativo': m.parlamentar.ativo}
            parlamentares.append(dict_parlamentar)

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all().order_by(
                '-data_inicio', '-data_fim'),
             'legislatura_id': int(form.data['periodo']),
             'form': form,
             'parlamentares': parlamentares})


class ParlamentaresCadastroView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_cadastro.html"

    def get_success_url(self):
        return reverse('parlamentares')

    def get(self, request, *args, **kwargs):
        form = ParlamentaresForm()

        pk = kwargs['pk']
        return self.render_to_response({'form': form, 'legislatura_id': pk})

    def post(self, request, *args, **kwargs):
        form = ParlamentaresForm(request.POST)

        pk = kwargs['pk']

        if form.is_valid():
            parlamentar = form.save(commit=False)
            if 'fotografia' in request.FILES:
                parlamentar.fotografia = request.FILES['fotografia']
                parlamentar.biografia = sub('&nbsp;',
                                            ' ',
                                            strip_tags(form.data['biografia']))
            parlamentar.save()

            mandato = Mandato()
            mandato.parlamentar = parlamentar
            mandato.legislatura = Legislatura.objects.get(id=pk)
            mandato.save()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form, 'legislatura_id': pk})


class DmitryImageField(ImageField):

    def to_python(self, data):
        f = super(DmitryImageField, self).to_python(data)
        if f is None:
            return None

        try:
            from PIL import Image
        except ImportError:
            import Image

        if hasattr(data, 'temporary_file_path'):
            file = data.temporary_file_path()
        else:
            if hasattr(data, 'read'):
                file = BytesIO(data.read())
            else:
                file = BytesIO(data['content'])

        try:
            im = Image.open(file)
            if im.format not in ('BMP', 'PNG', 'JPEG'):
                return -1
        except ImportError:
            return -2
        except Exception:
            return -3

        if hasattr(f, 'seek') and callable(f.seek):
            f.seek(0)
        return f


class ParlamentaresEditarView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_cadastro.html"

    def get_success_url(self):
        return reverse('parlamentares')

    def get(self, request, *args, **kwargs):
        pk = kwargs['pk']
        parlamentar = Parlamentar.objects.get(pk=pk)
        form = ParlamentaresEditForm(instance=parlamentar)
        return self.render_to_response(
            {'form': form, 'object': parlamentar})

    def post(self, request, *args, **kwargs):
        pk = kwargs['pk']
        parlamentar = Parlamentar.objects.get(pk=pk)
        form = ParlamentaresEditForm(request.POST, instance=parlamentar)

        if form.is_valid():
            if 'salvar' in request.POST:
                parlamentar = form.save(commit=False)
                if 'fotografia' in request.FILES:
                    parlamentar.fotografia = request.FILES['fotografia']
                valida_imagem = DmitryImageField()
                # import ipdb; ipdb.set_trace()
                try:
                    valida_imagem.to_python(request.FILES['fotografia'])
                except ValidationError:
                    mensagem = "Por favor, insira uma imagem válida dos formatos\
                    JPEG, PNG ou BMP"
                    messages.add_message(request, messages.INFO, mensagem)
                    return self.render_to_response({'form': form})
                else:
                    pass
                parlamentar.biografia = sub('&nbsp;',
                                            ' ',
                                            strip_tags(form.data['biografia']))
                parlamentar.save()
            elif 'excluir' in request.POST:
                Mandato.objects.get(parlamentar=parlamentar).delete()
                parlamentar.delete()
            elif "remover" in request.POST:
                try:
                    os.unlink(parlamentar.fotografia.path)
                except OSError:
                    pass  # Should log this error!!!!!
                parlamentar = form.save(commit=False)
                parlamentar.fotografia = None
                parlamentar.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})


class ParlamentaresDependentesView(FormMixin, GenericView):

    template_name = "parlamentares/parlamentares_dependentes.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares_dependentes', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        pid = kwargs['pk']
        parlamentar = Parlamentar.objects.get(id=pid)
        dependentes = Dependente.objects.filter(
            parlamentar=parlamentar).order_by('nome', 'tipo')

        form = DependenteForm()

        return self.render_to_response(
            {'object': parlamentar,
             'dependentes': dependentes,
             'form': form,
             'legislatura_id': parlamentar.mandato_set.last().legislatura.id})

    def post(self, request, *args, **kwargs):
        form = DependenteForm(request.POST)

        if form.is_valid():
            dependente = form.save(commit=False)

            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)
            dependente.parlamentar = parlamentar

            dependente.save()
            return self.form_valid(form)
        else:
            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)
            dependentes = Dependente.objects.filter(
                parlamentar=parlamentar).order_by('nome', 'tipo')

            return self.render_to_response(
                {'object': parlamentar,
                 'dependentes': dependentes,
                 'form': form,
                 'legislatura_id': parlamentar.mandato_set.last(
                 ).legislatura.id})


class ParlamentaresDependentesEditView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_dependentes_edit.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares_dependentes', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        dependente = Dependente.objects.get(id=kwargs['dk'])
        parlamentar = Parlamentar.objects.get(id=kwargs['pk'])
        form = DependenteEditForm(instance=dependente)
        return self.render_to_response(
            {'form': form,
             'object': parlamentar,
             'legislatura_id': dependente.parlamentar.mandato_set.last(
             ).legislatura_id})

    def post(self, request, *args, **kwargs):
        dependente = Dependente.objects.get(id=kwargs['dk'])
        form = DependenteEditForm(request.POST, instance=dependente)
        parlamentar = Parlamentar.objects.get(id=kwargs['pk'])

        if form.is_valid():
            if 'salvar' in request.POST:
                dependente.save()
            elif 'Excluir' in request.POST:
                dependente.delete()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': parlamentar,
                 'legislatura_id': dependente.parlamentar.mandato_set.last(
                 ).legislatura_id})


class MesaDiretoraView(FormMixin, GenericView):
    template_name = "mesa_diretora/mesa_diretora.html"

    def get_success_url(self):
        return reverse('mesa_diretora')

    # Essa função avisa quando se pode compor uma Mesa Legislativa)
    def validation(self, request):
        mensagem = "Não há nenhuma Sessão Legislativa cadastrada.\
        Só é possível compor uma Mesa Diretora quando há uma Sessão\
        Legislativa cadastrada."
        messages.add_message(request, messages.INFO, mensagem)

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-data_inicio'),
                'legislatura_selecionada': Legislatura.objects.last(),
                'cargos_vagos': CargoMesa.objects.all()})

    def get(self, request, *args, **kwargs):

        if (not Legislatura.objects.all() or
                not SessaoLegislativa.objects.all()):
            return self.validation(request)

        mesa = SessaoLegislativa.objects.filter(
            legislatura=Legislatura.objects.last()).first(
        ).composicaomesa_set.all()

        cargos_ocupados = [m.cargo for m in mesa]
        cargos = CargoMesa.objects.all()
        cargos_vagos = list(set(cargos) - set(cargos_ocupados))

        parlamentares = Legislatura.objects.last().mandato_set.all()
        parlamentares_ocupados = [m.parlamentar for m in mesa]
        parlamentares_vagos = list(
            set(
                [p.parlamentar for p in parlamentares]) - set(
                parlamentares_ocupados))

        return self.render_to_response(
            {'legislaturas': Legislatura.objects.all(
            ).order_by('-data_inicio'),
                'legislatura_selecionada': Legislatura.objects.last(),
                'sessoes': SessaoLegislativa.objects.filter(
                legislatura=Legislatura.objects.last()),
                'sessao_selecionada': SessaoLegislativa.objects.filter(
                legislatura=Legislatura.objects.last()).first(),
                'composicao_mesa': mesa,
                'parlamentares': parlamentares_vagos,
                'cargos_vagos': cargos_vagos
            })

    def post(self, request, *args, **kwargs):
        if 'Incluir' in request.POST:

            if (not Legislatura.objects.all() or
                    not SessaoLegislativa.objects.all()):
                return self.validation(request)

            composicao = ComposicaoMesa()
            composicao.sessao_legislativa = SessaoLegislativa.objects.get(
                id=int(request.POST['sessao']))
            composicao.parlamentar = Parlamentar.objects.get(
                id=int(request.POST['parlamentar']))
            composicao.cargo = CargoMesa.objects.get(
                id=int(request.POST['cargo']))
            composicao.save()

            return self.form_valid(form=None)
        elif 'Excluir' in request.POST:

            if (not Legislatura.objects.all() or
                    not SessaoLegislativa.objects.all()):
                return self.validation(request)

            if 'composicao_mesa' in request.POST:
                ids = request.POST['composicao_mesa'].split(':')
                composicao = ComposicaoMesa.objects.get(
                    sessao_legislativa_id=int(request.POST['sessao']),
                    parlamentar_id=int(ids[0]),
                    cargo_id=int(ids[1])
                )
                composicao.delete()
            return self.form_valid(form=None)
        else:
            mesa = ComposicaoMesa.objects.filter(
                sessao_legislativa=request.POST['sessao'])

            cargos_ocupados = [m.cargo for m in mesa]
            cargos = CargoMesa.objects.all()
            cargos_vagos = list(set(cargos) - set(cargos_ocupados))

            parlamentares = Legislatura.objects.get(
                id=int(request.POST['legislatura'])).mandato_set.all()
            parlamentares_ocupados = [m.parlamentar for m in mesa]
            parlamentares_vagos = list(
                set(
                    [p.parlamentar for p in parlamentares]) - set(
                    parlamentares_ocupados))
            return self.render_to_response(
                {'legislaturas': Legislatura.objects.all(
                ).order_by('-data_inicio'),
                    'legislatura_selecionada': Legislatura.objects.get(
                    id=int(request.POST['legislatura'])),
                    'sessoes': SessaoLegislativa.objects.filter(
                    legislatura_id=int(request.POST['legislatura'])),
                    'sessao_selecionada': SessaoLegislativa.objects.get(
                    id=int(request.POST['sessao'])),
                    'composicao_mesa': mesa,
                    'parlamentares': parlamentares_vagos,
                    'cargos_vagos': cargos_vagos
                })


class FiliacaoView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_filiacao.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares_filiacao', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        pid = kwargs['pk']
        parlamentar = Parlamentar.objects.get(id=pid)
        filiacoes = Filiacao.objects.filter(
            parlamentar=parlamentar)

        form = FiliacaoForm()

        return self.render_to_response(
            {'object': parlamentar,
             'filiacoes': filiacoes,
             'form': form,
             'legislatura_id': parlamentar.mandato_set.last().legislatura.id})

    # Função usada para todos os caso de erro na filiação
    def error_message(self, parlamentar, form, mensagem, request):
        filiacoes = Filiacao.objects.filter(parlamentar=parlamentar)
        messages.add_message(request, messages.INFO, mensagem)
        return self.render_to_response(
            {'object': parlamentar,
             'filiacoes': filiacoes,
             'form': form,
             'legislatura_id': parlamentar.mandato_set.last(
             ).legislatura.id})

    def post(self, request, *args, **kwargs):
        form = FiliacaoForm(request.POST)

        if form.is_valid():

            data_filiacao = form.cleaned_data['data']
            data_desfiliacao = form.cleaned_data['data_desfiliacao']

            filiacao = form.save(commit=False)
            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)

            candidato_filiado = Filiacao.objects.filter(
                parlamentar=parlamentar)

            candidato_nao_desfiliou = Filiacao.objects.filter(
                parlamentar=parlamentar,
                data_desfiliacao=None)

            # Vê se o candidato já se filiou alguma vez a algum partido
            if not candidato_filiado:
                filiacao = form.save(commit=False)
                filiacao.parlamentar = parlamentar
                filiacao.save()
                return self.form_valid(form)
            else:
                # Dá erro caso não tenha se desfiliado do anterior
                if candidato_nao_desfiliou:
                    mensagem = "Você não pode se filiar a algum partido\
                    sem antes se desfiliar do partido anterior"
                    return self.error_message(
                        parlamentar, form, mensagem, request)

                # Dá erro caso a data de desfiliação seja anterior a de
                # filiação
                if data_desfiliacao and data_desfiliacao < data_filiacao:
                    mensagem = "A data de filiação não pode ser\
                    anterior à data de desfiliação"
                    return self.error_message(
                        parlamentar, form, mensagem, request)

                # Esse bloco garante que não haverá intersecção entre os
                # períodos de filiação
                todas_filiacoes = candidato_filiado
                for i in range(len(todas_filiacoes)):
                    data_init = todas_filiacoes[i].data
                    data_fim = todas_filiacoes[i].data_desfiliacao
                    if data_filiacao >= data_init and data_filiacao < data_fim:
                        mensagem = "A data de filiação e\
                        desfiliação não podem estar no intervalo\
                        de outro período de filiação"
                        return self.error_message(
                            parlamentar, form, mensagem, request)

                    if (data_desfiliacao and
                            data_desfiliacao < data_fim and
                            data_desfiliacao > data_init):

                        mensagem = "A data de filiação e\
                        desfiliação não podem estar no intervalo\
                        de outro período de filiação"
                        return self.error_message(
                            parlamentar, form, mensagem, request)

                    if (data_desfiliacao and
                            data_filiacao <= data_init and
                            data_desfiliacao >= data_fim):
                        mensagem = "A data de filiação e\
                        desfiliação não podem estar no intervalo\
                        de outro período de filiação"
                        return self.error_message(
                            parlamentar, form, mensagem, request)

                # Salva a nova filiação caso tudo esteja correto
                else:
                    filiacao = form.save(commit=False)
                    filiacao.parlamentar = parlamentar
                    filiacao.save()
                    return self.form_valid(form)
        else:
            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)
            mensagem = ""
            return self.error_message(
                parlamentar, form, mensagem, request)


class FiliacaoEditView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_filiacao_edit.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares_filiacao', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        filiacao = Filiacao.objects.get(id=kwargs['dk'])
        parlamentar = Parlamentar.objects.get(id=kwargs['pk'])
        form = FiliacaoEditForm(instance=filiacao)
        return self.render_to_response(
            {'form': form,
             'object': parlamentar,
             'legislatura_id': parlamentar.mandato_set.last(
             ).legislatura_id})

    def error_message(self, parlamentar, form, mensagem, request):
        messages.add_message(request, messages.INFO, mensagem)
        return self.render_to_response(
            {'form': form,
             'object': parlamentar,
             'legislatura_id': parlamentar.mandato_set.last(
             ).legislatura_id})

    def post(self, request, *args, **kwargs):
        filiacao = Filiacao.objects.get(id=kwargs['dk'])
        form = FiliacaoEditForm(request.POST, instance=filiacao)
        parlamentar = Parlamentar.objects.get(id=kwargs['pk'])

        if form.is_valid():

            data_filiacao = form.cleaned_data['data']
            data_desfiliacao = form.cleaned_data['data_desfiliacao']

            filiacao = form.save(commit=False)
            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)

            candidato_filiado = Filiacao.objects.filter(
                parlamentar=parlamentar)

            if 'Excluir' in request.POST:
                filiacao.delete()
                return self.form_valid(form)

            # Vê se o candidato já se filiou alguma vez a algum partido
            if not candidato_filiado:
                filiacao = form.save(commit=False)
                filiacao.parlamentar = parlamentar
                filiacao.save()
                return self.form_valid(form)
            else:

                # Dá erro caso a data de desfiliação seja anterior a de
                # filiação
                if data_desfiliacao and data_desfiliacao < data_filiacao:
                    mensagem = "A data de filiação não pode\
                    anterior à data de desfiliação"
                    return self.error_message(
                        parlamentar, form, mensagem, request)

                # Esse bloco garante que não haverá intersecção entre os
                # períodos de filiação
                todas_filiacoes = candidato_filiado
                id_filiacao_atual = int(kwargs['dk'])
                for i in range(len(todas_filiacoes)):
                    if todas_filiacoes[i].id != id_filiacao_atual:
                        data_init = todas_filiacoes[i].data
                        data_fim = todas_filiacoes[i].data_desfiliacao
                        if (data_filiacao >= data_init and
                                data_filiacao < data_fim):

                            mensagem = "A data de filiação e\
                            desfiliação não podem estar no intervalo\
                            de outro período de filiação"
                            return self.error_message(parlamentar,
                                                      form,
                                                      mensagem,
                                                      request)

                        if (data_desfiliacao and
                                data_desfiliacao < data_fim and
                                data_desfiliacao > data_init):

                            mensagem = "A data de filiação e\
                            desfiliação não podem estar no intervalo\
                            de outro período de filiação"
                            return self.error_message(parlamentar,
                                                      form,
                                                      mensagem,
                                                      request)
                        if (data_desfiliacao and
                                data_filiacao <= data_init and
                                data_desfiliacao >= data_fim):
                            mensagem = "A data de filiação e\
                            desfiliação não podem estar no intervalo\
                            de outro período de filiação"
                            return self.error_message(parlamentar,
                                                      form,
                                                      mensagem,
                                                      request)

            if 'salvar' in request.POST:
                filiacao.save()
            elif 'Excluir' in request.POST:
                filiacao.delete()
            return self.form_valid(form)

        else:
            return self.render_to_response(
                {'form': form,
                 'object': parlamentar,
                 'legislatura_id': parlamentar.mandato_set.last(
                 ).legislatura_id})


class MandatoView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_mandato.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares_mandato', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        pid = kwargs['pk']
        parlamentar = Parlamentar.objects.get(id=pid)
        mandatos = Mandato.objects.filter(
            parlamentar=parlamentar)

        form = MandatoForm()

        return self.render_to_response(
            {'object': parlamentar,
             'mandatos': mandatos,
             'form': form,
             'legislatura_id': parlamentar.mandato_set.last().legislatura.id})

    def post(self, request, *args, **kwargs):
        form = MandatoForm(request.POST)

        if form.is_valid():
            mandato = form.save(commit=False)

            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)
            mandato.parlamentar = parlamentar

            mandato.save()
            return self.form_valid(form)
        else:
            pid = kwargs['pk']
            parlamentar = Parlamentar.objects.get(id=pid)
            mandatos = Mandato.objects.filter(
                parlamentar=parlamentar)

            return self.render_to_response(
                {'object': parlamentar,
                 'mandatos': mandatos,
                 'form': form,
                 'legislatura_id': parlamentar.mandato_set.last(
                 ).legislatura.id})


class MandatoEditView(FormMixin, GenericView):
    template_name = "parlamentares/parlamentares_mandato_edit.html"

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares_mandato', kwargs={'pk': pk})

    def get(self, request, *args, **kwargs):
        mandato = Mandato.objects.get(id=kwargs['dk'])
        parlamentar = Parlamentar.objects.get(id=kwargs['pk'])
        form = MandatoEditForm(instance=mandato)
        return self.render_to_response(
            {'form': form,
             'object': parlamentar,
             'legislatura_id': parlamentar.mandato_set.last(
             ).legislatura_id})

    def post(self, request, *args, **kwargs):
        mandato = Mandato.objects.get(id=kwargs['dk'])
        form = MandatoEditForm(request.POST, instance=mandato)
        parlamentar = Parlamentar.objects.get(id=kwargs['pk'])

        if form.is_valid():
            if 'salvar' in request.POST:
                mandato.save()
            elif 'Excluir' in request.POST:
                mandato.delete()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': parlamentar,
                 'legislatura_id': parlamentar.mandato_set.last(
                 ).legislatura_id})
