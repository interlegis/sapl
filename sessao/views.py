from datetime import datetime
from re import sub

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

import sapl
from materia.models import Autoria, TipoMateriaLegislativa
from parlamentares.models import Parlamentar
from sapl.crud import build_crud

from .models import (CargoMesa, ExpedienteMateria, ExpedienteSessao,
                     IntegranteMesa, MateriaLegislativa, Orador,
                     OradorExpediente, OrdemDia, PresencaOrdemDia,
                     RegistroVotacao, SessaoPlenaria, SessaoPlenariaPresenca,
                     TipoExpediente, TipoResultadoVotacao, TipoSessaoPlenaria,
                     VotoParlamentar)

tipo_sessao_crud = build_crud(
    TipoSessaoPlenaria, 'tipo_sessao_plenaria', [

        [_('Tipo de Sessão Plenária'),
         [('nome', 6), ('quorum_minimo', 6)]],
    ])

sessao_crud = build_crud(
    SessaoPlenaria, '', [

        [_('Dados Básicos'),
         [('numero', 1),
            ('tipo', 3),
            ('legislatura', 4),
            ('sessao_legislativa', 4)],
            [('data_inicio', 5), ('hora_inicio', 5), ('iniciada', 2)],
            [('data_fim', 5), ('hora_fim', 5), ('finalizada', 2)],
            [('upload_pauta', 6), ('upload_ata', 6)],
            [('url_audio', 6), ('url_video', 6)]],
    ])

expediente_materia_crud = build_crud(
    ExpedienteMateria, '', [

        [_('Cadastro de Matérias do Expediente'),
         [('data_ordem', 4), ('tip_sessao_FIXME', 4), ('numero_ordem', 4)],
            [('tip_id_basica_FIXME', 4),
             ('num_ident_basica_FIXME', 4),
             ('ano_ident_basica_FIXME', 4)],
            [('tipo_votacao', 12)],
            [('observacao', 12)]],
    ])

ordem_dia_crud = build_crud(
    OrdemDia, '', [

        [_('Cadastro de Matérias da Ordem do Dia'),
         [('data_ordem', 4), ('tip_sessao_FIXME', 4), ('numero_ordem', 4)],
            [('tip_id_basica_FIXME', 4),
             ('num_ident_basica_FIXME', 4),
             ('ano_ident_basica_FIXME', 4)],
            [('tipo_votacao', 12)],
            [('observacao', 12)]],
    ])

tipo_resultado_votacao_crud = build_crud(
    TipoResultadoVotacao, 'tipo_resultado_votacao', [

        [_('Tipo de Resultado da Votação'),
         [('nome', 12)]],
    ])

tipo_expediente_crud = build_crud(
    TipoExpediente, 'tipo_expediente', [

        [_('Tipo de Expediente'),
         [('nome', 12)]],
    ])

registro_votacao_crud = build_crud(
    RegistroVotacao, '', [

        [_('Votação Simbólica'),
         [('numero_votos_sim', 3),
            ('numero_votos_nao', 3),
            ('numero_abstencoes', 3),
            ('nao_votou_FIXME', 3)],
            [('votacao_branco_FIXME', 6),
             ('ind_votacao_presidente_FIXME', 6)],
            [('tipo_resultado_votacao', 12)],
            [('observacao', 12)]],
    ])


class PresencaForm(forms.Form):
    presenca = forms.CharField(required=False, initial=False)
    parlamentar = forms.CharField(required=False, max_length=20)


class PresencaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/presenca.html'
    form_class = PresencaForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.object.id)

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca')

            # Deletar os que foram desmarcadors
            deletar = set(set(presentes_banco) - set(marcados))
            for d in deletar:
                SessaoPlenariaPresenca.objects.filter(
                    parlamentar_id=d.parlamentar_id).delete()

            for p in marcados:
                sessao = SessaoPlenariaPresenca()
                sessao.sessao_plenaria = self.object
                sessao.parlamentar = Parlamentar.objects.get(id=p)
                sessao.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield (parlamentar, True)
            else:
                yield (parlamentar, False)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:presenca', kwargs={'pk': pk})


class PainelView(sessao_crud.CrudDetailView):
    template_name = 'sessao/painel.html'


class PresencaOrdemDiaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/presenca_ordemdia.html'
    form_class = PresencaForm

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = self.get_form()

        pk = kwargs['pk']

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=pk)

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca')

            # Deletar os que foram desmarcadors
            deletar = set(set(presentes_banco) - set(marcados))
            for d in deletar:
                PresencaOrdemDia.objects.filter(
                    parlamentar_id=d.parlamentar_id).delete()

            for p in marcados:
                ordem = PresencaOrdemDia()
                ordem.sessao_plenaria = self.object
                ordem.parlamentar = Parlamentar.objects.get(id=p)
                ordem.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )

        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield (parlamentar, True)
            else:
                yield (parlamentar, False)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:presencaordemdia', kwargs={'pk': pk})


class ListMateriaForm(forms.Form):
    error_message = forms.CharField(required=False, label='votacao_aberta')


class ListMateriaOrdemDiaView(sessao_crud.CrudDetailView):
    template_name = 'sessao/materia_ordemdia_list.html'
    form_class = ListMateriaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        ordem = OrdemDia.objects.filter(sessao_plenaria_id=pk)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            autoria = Autoria.objects.filter(materia_id=o.materia_id)
            autor = [str(a.autor) for a in autoria]

            mat = {'pk': pk,
                   'oid': o.materia_id,
                   'ordem_id': o.id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': o.resultado,
                   'autor': autor,
                   'votacao_aberta': o.votacao_aberta,
                   'tipo_votacao': o.tipo_votacao
                   }
            materias_ordem.append(mat)

        sorted(materias_ordem, key=lambda x: x['numero'])

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        form = ListMateriaForm(request.POST)

        # TODO: Existe uma forma de atualizar em lote de acordo
        # com a forma abaixo, mas como setar o primeiro para "1"?
        # OrdemDia.objects.filter(sessao_plenaria_id=pk)
        # .order_by('numero_ordem').update(numero_ordem=3)

        if 'materia_reorder' in request.POST:
            ordens = OrdemDia.objects.filter(sessao_plenaria_id=pk)
            ordem_num = 1
            for o in ordens:
                o.numero_ordem = ordem_num
                o.save()
                ordem_num += 1
        elif 'abrir-votacao' in request.POST:
            existe_votacao_aberta = OrdemDia.objects.filter(
                sessao_plenaria_id=pk, votacao_aberta=True).exists()
            if existe_votacao_aberta:
                context = self.get_context_data(object=self.object)

                form._errors = {'error_message': 'error_message'}
                context.update({'form': form})

                pk = self.kwargs['pk']
                ordem = OrdemDia.objects.filter(sessao_plenaria_id=pk)

                materias_ordem = []
                for o in ordem:
                    ementa = o.observacao
                    titulo = o.materia
                    numero = o.numero_ordem

                    autoria = Autoria.objects.filter(materia_id=o.materia_id)
                    autor = [str(a.autor) for a in autoria]

                    mat = {'pk': pk,
                           'oid': o.materia_id,
                           'ordem_id': o.id,
                           'ementa': ementa,
                           'titulo': titulo,
                           'numero': numero,
                           'resultado': o.resultado,
                           'autor': autor,
                           'votacao_aberta': o.votacao_aberta,
                           'tipo_votacao': o.tipo_votacao
                           }
                    materias_ordem.append(mat)

                sorted(materias_ordem, key=lambda x: x['numero'])
                context.update({'materias_ordem': materias_ordem})
                return self.render_to_response(context)
            else:
                ordem_id = request.POST['ordem_id']
                ordem = OrdemDia.objects.get(id=ordem_id)
                ordem.votacao_aberta = True
                ordem.save()
        return self.get(self, request, args, kwargs)


class ListExpedienteOrdemDiaView(sessao_crud.CrudDetailView):
    template_name = 'sessao/expediente_ordemdia_list.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = self.kwargs['pk']
        ordem = ExpedienteMateria.objects.filter(sessao_plenaria_id=pk)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            autoria = Autoria.objects.filter(materia_id=o.materia_id)
            autor = [str(a.autor) for a in autoria]

            mat = {'pk': pk,
                   'oid': o.materia_id,
                   'ordem_id': o.id,
                   'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': o.resultado,
                   'autor': autor,
                   'votacao_aberta': o.votacao_aberta,
                   'tipo_votacao': o.tipo_votacao
                   }
            materias_ordem.append(mat)

        sorted(materias_ordem, key=lambda x: x['numero'])

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        pk = self.kwargs['pk']
        form = ListMateriaForm(request.POST)

        if 'materia_reorder' in request.POST:
            expedientes = ExpedienteMateria.objects.filter(
                sessao_plenaria_id=pk)
            exp_num = 1
            for e in expedientes:
                e.numero_ordem = exp_num
                e.save()
                exp_num += 1
        elif 'abrir-votacao' in request.POST:
            existe_votacao_aberta = ExpedienteMateria.objects.filter(
                sessao_plenaria_id=pk, votacao_aberta=True
            ).exists()

            if existe_votacao_aberta:
                context = self.get_context_data(object=self.object)

                form._errors = {'error_message': 'error_message'}
                context.update({'form': form})

                pk = self.kwargs['pk']
                ordem = ExpedienteMateria.objects.filter(
                    sessao_plenaria_id=pk)

                materias_ordem = []
                for o in ordem:
                    ementa = o.observacao
                    titulo = o.materia
                    numero = o.numero_ordem

                    autoria = Autoria.objects.filter(materia_id=o.materia_id)
                    autor = [str(a.autor) for a in autoria]

                    mat = {'pk': pk,
                           'oid': o.materia_id,
                           'ordem_id': o.id,
                           'ementa': ementa,
                           'titulo': titulo,
                           'numero': numero,
                           'resultado': o.resultado,
                           'autor': autor,
                           'votacao_aberta': o.votacao_aberta,
                           'tipo_votacao': o.tipo_votacao
                           }
                    materias_ordem.append(mat)

                sorted(materias_ordem, key=lambda x: x['numero'])

                context.update({'materias_ordem': materias_ordem})
                return self.render_to_response(context)
            else:
                ordem_id = request.POST['ordem_id']
                ordem = ExpedienteMateria.objects.get(id=ordem_id)
                ordem.votacao_aberta = True
                ordem.save()
        return self.get(self, request, args, kwargs)


class MateriaOrdemDiaForm(forms.Form):
    data_sessao = forms.CharField(required=True, label='Data da Sessão')
    numero_ordem = forms.IntegerField(required=True, label='Número Ordem')
    tipo_votacao = forms.IntegerField(required=True, label='Tipo Votação')
    tipo_sessao = forms.IntegerField(required=True, label='Tipo da Sessão')
    ano_materia = forms.IntegerField(required=True, label='Ano Matéria')
    numero_materia = forms.IntegerField(required=True, label='Número Matéria')
    tipo_materia = forms.IntegerField(required=True, label='Tipo Matéria')
    observacao = forms.CharField(required=False, label='Ementa')
    error_message = forms.CharField(required=False, label='Matéria')


class MateriaOrdemDiaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/materia_ordemdia.html'
    form_class = MateriaOrdemDiaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        now = datetime.now()

        tipo_materia = TipoMateriaLegislativa.objects.all()
        data_sessao = now
        tipo_sessao = TipoSessaoPlenaria.objects.all()
        tipo_votacao = ExpedienteMateria.TIPO_VOTACAO_CHOICES
        ano_materia = now.year

        context.update({'data_sessao': data_sessao,
                        'tipo_sessao': tipo_sessao,
                        'tipo_materia': tipo_materia,
                        'tipo_votacao': tipo_votacao,
                        'ano_materia': ano_materia,
                        'error_message': '', })
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        form = MateriaOrdemDiaForm(request.POST)

        if form.is_valid():
            try:
                materia = MateriaLegislativa.objects.get(
                    numero=request.POST['numero_materia'],
                    tipo_id=request.POST['tipo_materia'],
                    ano=request.POST['ano_materia'])
            except ObjectDoesNotExist:
                form._errors["error_message"] = ErrorList([u""])
                context.update({'form': form})
                return self.render_to_response(context)

            # TODO: barrar matérias não existentes
            # TODO: barrar criação de ordemdia para materias já incluídas

            ordemdia = OrdemDia()
            ordemdia.sessao_plenaria_id = self.object.id
            ordemdia.materia_id = materia.id
            ordemdia.numero_ordem = request.POST['numero_ordem']
            ordemdia.data_ordem = datetime.now()
            ordemdia.observacao = sub('&nbsp;', ' ',
                                      strip_tags(request.POST['observacao']))
            ordemdia.tipo_votacao = request.POST['tipo_votacao']
            ordemdia.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:materiaordemdia_list',
                       kwargs={'pk': pk})


class EditMateriaOrdemDiaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/materia_ordemdia_edit.html'
    form_class = MateriaOrdemDiaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = kwargs['pk']
        oid = kwargs['oid']
        ordem = OrdemDia.objects.get(sessao_plenaria_id=pk, materia_id=oid)

        materia = MateriaLegislativa.objects.get(
            id=ordem.materia_id)

        data_ordem = ordem.data_ordem
        tipo_votacao = ExpedienteMateria.TIPO_VOTACAO_CHOICES
        tipo_sessao = TipoSessaoPlenaria.objects.all()
        tipo_materia = TipoMateriaLegislativa.objects.all()

        context.update({'data_sessao': data_ordem,
                        'tipo_sessao': tipo_sessao,
                        'tipo_sessao_selected': self.object.tipo,
                        'tipo_materia': tipo_materia,
                        'tipo_materia_selected': materia.tipo,
                        'tipo_votacao': tipo_votacao,
                        'tipo_votacao_selected': ordem.tipo_votacao,
                        'ano_materia': materia.ano,
                        'numero_ordem': ordem.numero_ordem,
                        'numero_materia': materia.numero,
                        'ordem_id': oid,
                        'oid': '',
                        'observacao': sub(
                            '&nbsp;', ' ', strip_tags(ordem.observacao)),
                        'error_message': '', })
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        form = MateriaOrdemDiaForm(request.POST)

        pk = kwargs['pk']
        oid = kwargs['oid']
        ordemdia = OrdemDia.objects.get(sessao_plenaria_id=pk, materia_id=oid)

        if 'update-ordemdia' in request.POST:
            if form.is_valid():
                try:
                    materia = MateriaLegislativa.objects.get(
                        numero=request.POST['numero_materia'],
                        tipo_id=request.POST['tipo_materia'],
                        ano=request.POST['ano_materia'])
                except ObjectDoesNotExist:
                    context.update(
                        {'error_message': "Matéria inexistente!"})
                    return self.form_invalid(form)

                ordemdia.materia_id = materia.id
                ordemdia.numero_ordem = request.POST['numero_ordem']
                ordemdia.tipo_votacao = request.POST['tipo_votacao']
                obs = strip_tags(request.POST['observacao'])
                ordemdia.observacao = sub('&nbsp;', '  ', obs)
                ordemdia.save()
                return self.form_valid(form)
            else:
                context = self.get_context_data(object=self.object)

                pk = kwargs['pk']
                oid = kwargs['oid']
                ordem = OrdemDia.objects.get(
                    sessao_plenaria_id=pk,
                    materia_id=oid)

                materia = MateriaLegislativa.objects.get(
                    id=ordem.materia_id)

                data_ordem = ordem.data_ordem
                tipo_votacao = ExpedienteMateria.TIPO_VOTACAO_CHOICES
                tipo_sessao = TipoSessaoPlenaria.objects.all()
                tipo_materia = TipoMateriaLegislativa.objects.all()

                context.update({'data_sessao': data_ordem,
                                'tipo_sessao': tipo_sessao,
                                'tipo_sessao_selected': self.object.tipo,
                                'tipo_materia': tipo_materia,
                                'tipo_materia_selected': materia.tipo,
                                'tipo_votacao': tipo_votacao,
                                'tipo_votacao_selected': ordem.tipo_votacao,
                                'ano_materia': materia.ano,
                                'numero_ordem': ordem.numero_ordem,
                                'numero_materia': materia.numero,
                                'ordem_id': oid,
                                'oid': '',
                                'observacao': sub(
                                    '&nbsp;', ' ',
                                    strip_tags(ordem.observacao)),
                                'error_message': '', })
                context.update({'form': form})
                return self.render_to_response(context)
        elif 'delete-ordemdia' in request.POST:
            ordemdia.delete()
            return self.form_valid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:materiaordemdia_list',
                       kwargs={'pk': pk})


class ExpedienteOrdemDiaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/materia_ordemdia.html'
    form_class = MateriaOrdemDiaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        now = datetime.now()

        tipo_materia = TipoMateriaLegislativa.objects.all()
        data_sessao = now
        tipo_sessao = TipoSessaoPlenaria.objects.all()
        tipo_votacao = ExpedienteMateria.TIPO_VOTACAO_CHOICES
        ano_materia = now.year

        context.update({'data_sessao': data_sessao,
                        'tipo_sessao': tipo_sessao,
                        'tipo_materia': tipo_materia,
                        'tipo_votacao': tipo_votacao,
                        'ano_materia': ano_materia,
                        'error_message': '', })
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        form = MateriaOrdemDiaForm(request.POST)

        if form.is_valid():
            try:
                materia = MateriaLegislativa.objects.get(
                    numero=request.POST['numero_materia'],
                    tipo_id=request.POST['tipo_materia'],
                    ano=request.POST['ano_materia'])
            except ObjectDoesNotExist:
                form._errors["error_message"] = ErrorList([u""])
                context.update({'form': form})
                return self.render_to_response(context)

            # TODO: barrar matérias não existentes
            # TODO: barrar criação de ordemdia para materias já incluídas

            ordemdia = ExpedienteMateria()
            ordemdia.sessao_plenaria_id = self.object.id
            ordemdia.materia_id = materia.id
            ordemdia.numero_ordem = request.POST['numero_ordem']
            ordemdia.data_ordem = datetime.now()
            ordemdia.observacao = sub('&nbsp;', ' ',
                                      strip_tags(request.POST['observacao']))
            ordemdia.tipo_votacao = request.POST['tipo_votacao']
            ordemdia.save()

            return self.form_valid(form)
        else:
            context.update(
                {'error_message': "Não foi possível salvar formulário!"})
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expedienteordemdia_list',
                       kwargs={'pk': pk})


class EditExpedienteOrdemDiaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/materia_ordemdia_edit.html'
    form_class = MateriaOrdemDiaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        pk = kwargs['pk']
        oid = kwargs['oid']
        ordem = ExpedienteMateria.objects.get(
            sessao_plenaria_id=pk, materia_id=oid)

        materia = MateriaLegislativa.objects.get(
            id=ordem.materia_id)

        data_ordem = ordem.data_ordem
        tipo_votacao = ExpedienteMateria.TIPO_VOTACAO_CHOICES
        tipo_sessao = TipoSessaoPlenaria.objects.all()
        tipo_materia = TipoMateriaLegislativa.objects.all()

        context.update({'data_sessao': data_ordem,
                        'tipo_sessao': tipo_sessao,
                        'tipo_sessao_selected': self.object.tipo,
                        'tipo_materia': tipo_materia,
                        'tipo_materia_selected': materia.tipo,
                        'tipo_votacao': tipo_votacao,
                        'tipo_votacao_selected': ordem.tipo_votacao,
                        'ano_materia': materia.ano,
                        'numero_ordem': ordem.numero_ordem,
                        'numero_materia': materia.numero,
                        'ordem_id': oid,
                        'oid': '',
                        'observacao': sub(
                            '&nbsp;', ' ', strip_tags(ordem.observacao)),
                        'error_message': '', })
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        form = MateriaOrdemDiaForm(request.POST)

        pk = kwargs['pk']
        oid = kwargs['oid']
        ordemdia = ExpedienteMateria.objects.get(
            sessao_plenaria_id=pk, materia_id=oid)

        if 'update-ordemdia' in request.POST:
            if form.is_valid():
                try:
                    materia = MateriaLegislativa.objects.get(
                        numero=request.POST['numero_materia'],
                        tipo_id=request.POST['tipo_materia'],
                        ano=request.POST['ano_materia'])
                except ObjectDoesNotExist:
                    context.update(
                        {'error_message': "Matéria inexistente!"})
                    return self.form_invalid(form)

                ordemdia.materia_id = materia.id
                ordemdia.numero_ordem = request.POST['numero_ordem']
                ordemdia.tipo_votacao = request.POST['tipo_votacao']
                obs = strip_tags(request.POST['observacao'])
                ordemdia.observacao = sub('&nbsp;', '  ', obs)
                ordemdia.save()
                return self.form_valid(form)
            else:
                context.update(
                    {'error_message': "Não foi possível salvar formulário!"})
                return self.form_invalid(form)
        elif 'delete-ordemdia' in request.POST:
            ordemdia.delete()
            return self.form_valid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expedienteordemdia_list',
                       kwargs={'pk': pk})


class OradorForm(forms.Form):
    numero_ordem = forms.IntegerField(
        required=True,
        label='Ordem de pronunciamento')
    parlamentar = forms.CharField(required=False, max_length=20)
    url_discurso = forms.CharField(required=False, max_length=100)


class OradorDeleteForm(forms.Form):
    pass


class OradorExpedienteDelete(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/delete_orador.html'
    form_class = OradorDeleteForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        orador_id = kwargs['oid']

        form = OradorDeleteForm(request.POST)

        if form.is_valid():
            orador = OradorExpediente.objects.get(
                sessao_plenaria_id=self.object.id,
                parlamentar_id=orador_id)
            orador.delete()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:oradorexpediente', kwargs={'pk': pk})


class OradorExpedienteEdit(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/edit_orador.html'
    form_class = OradorForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OradorForm(request.POST)

        if form.is_valid():
            orador_id = kwargs['oid']

            orador = OradorExpediente.objects.get(
                sessao_plenaria_id=self.object.id,
                parlamentar_id=orador_id)
            orador.delete()

            orador = OradorExpediente()
            orador.sessao_plenaria_id = self.object.id
            orador.numero_ordem = request.POST['numero_ordem']
            orador.parlamentar = Parlamentar.objects.get(
                id=orador_id)
            orador.url_discurso = request.POST['url_discurso']
            orador.save()

            return self.form_valid(form)
        else:
            context = self.get_context_data(object=self.object)
            orador_id = kwargs['oid']

            parlamentar = Parlamentar.objects.get(id=orador_id)
            orador = OradorExpediente.objects.get(
                sessao_plenaria=self.object, parlamentar=parlamentar)

            orador = {'parlamentar': parlamentar,
                      'url_discurso': orador.url_discurso}
            context.update({'orador': orador})
            context.update({'form': form})
            return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        orador_id = kwargs['oid']

        parlamentar = Parlamentar.objects.get(id=orador_id)
        orador = OradorExpediente.objects.get(
            sessao_plenaria=self.object, parlamentar=parlamentar)

        orador = {'parlamentar': parlamentar, 'numero_ordem':
                  orador.numero_ordem, 'url_discurso': orador.url_discurso}
        context.update({'orador': orador})

        return self.render_to_response(context)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:oradorexpediente', kwargs={'pk': pk})


class OradorExpedienteView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/orador_expediente.html'
    form_class = OradorForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OradorForm(request.POST)

        if 'adicionar' in request.POST:
            if form.is_valid():
                orador = OradorExpediente()
                orador.sessao_plenaria_id = self.object.id
                orador.numero_ordem = request.POST['numero_ordem']
                orador.parlamentar = Parlamentar.objects.get(
                    id=request.POST['parlamentar'])
                orador.url_discurso = request.POST['url_discurso']
                orador.save()
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        elif 'reordenar' in request.POST:
            orador = OradorExpediente.objects.filter(
                sessao_plenaria_id=self.object.id)
            ordem_num = 1
            for o in orador:
                o.numero_ordem = ordem_num
                o.save()
                ordem_num += 1
            return self.get(self, request, args, kwargs)

    def get_candidatos_orador(self):
        self.object = self.get_object()
        lista_parlamentares = []
        lista_oradores = []

        for parlamentar in Parlamentar.objects.all():
            if parlamentar.ativo:
                lista_parlamentares.append(parlamentar)

        for orador in OradorExpediente.objects.filter(
                sessao_plenaria_id=self.object.id):
            parlamentar = Parlamentar.objects.get(
                id=orador.parlamentar_id)
            lista_oradores.append(parlamentar)

        lista = list(set(lista_parlamentares) - set(lista_oradores))
        lista.sort(key=lambda x: x.nome_parlamentar)
        return lista

    def get_oradores(self):
        self.object = self.get_object()

        for orador in OradorExpediente.objects.filter(
                sessao_plenaria_id=self.object.id):
            numero_ordem = orador.numero_ordem
            url_discurso = orador.url_discurso
            parlamentar = Parlamentar.objects.get(
                id=orador.parlamentar_id)
            yield(numero_ordem, url_discurso, parlamentar)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:oradorexpediente', kwargs={'pk': pk})


class MesaForm(forms.Form):
    parlamentar = forms.IntegerField(required=True)
    cargo = forms.IntegerField(required=True)


class MesaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/mesa.html'
    form_class = MesaForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        mesa = IntegranteMesa.objects.filter(
            sessao_plenaria=self.object)

        integrantes = []
        for m in mesa:
            parlamentar = Parlamentar.objects.get(
                id=m.parlamentar_id)
            cargo = CargoMesa.objects.get(
                id=m.cargo_id)
            integrante = {'parlamentar': parlamentar, 'cargo': cargo}
            integrantes.append(integrante)

        context.update({'integrantes': integrantes})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MesaForm(request.POST)

        if 'Incluir' in request.POST:
            if form.is_valid():
                integrante = IntegranteMesa()
                integrante.sessao_plenaria_id = self.object.id
                integrante.parlamentar_id = request.POST['parlamentar']
                integrante.cargo_id = request.POST['cargo']
                integrante.save()

                return self.form_valid(form)

            else:
                form.clean()
                return self.form_valid(form)
        elif 'Excluir' in request.POST:
            if 'composicao_mesa' in request.POST:
                ids = request.POST['composicao_mesa'].split(':')
                IntegranteMesa.objects.get(
                    sessao_plenaria_id=self.object.id,
                    parlamentar_id=ids[0],
                    cargo_id=ids[1]
                ).delete()
            else:
                pass
                # TODO display message asking to select a member of list

        return self.form_valid(form)

    def get_candidatos_mesa(self):
        self.object = self.get_object()
        lista_parlamentares = []
        lista_integrantes = []

        for parlamentar in Parlamentar.objects.all():
            if parlamentar.ativo:
                lista_parlamentares.append(parlamentar)

        for integrante in IntegranteMesa.objects.filter(
                sessao_plenaria=self.object):
            parlamentar = Parlamentar.objects.get(
                id=integrante.parlamentar_id)
            lista_integrantes.append(parlamentar)

        lista = list(set(lista_parlamentares) - set(lista_integrantes))
        lista.sort(key=lambda x: x.nome_parlamentar)
        return lista

    def get_cargos_mesa(self):
        self.object = self.get_object()
        lista_cargos = CargoMesa.objects.all()
        lista_cargos_ocupados = []

        for integrante in IntegranteMesa.objects.filter(
                sessao_plenaria=self.object):
            cargo = CargoMesa.objects.get(
                id=integrante.cargo_id)
            lista_cargos_ocupados.append(cargo)

        lista = list(set(lista_cargos) - set(lista_cargos_ocupados))
        lista.sort(key=lambda x: x.descricao)
        return lista

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:mesa', kwargs={'pk': pk})


class ResumoView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/resumo.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # =====================================================================
        # Identificação Básica
        abertura = self.object.data_inicio.strftime('%d/%m/%Y')
        encerramento = self.object.data_fim.strftime('%d/%m/%Y')

        context.update({'basica': ['Tipo de Sessão: ' + str(self.object.tipo),
                                   'Abertura: ' + abertura,
                                   'Encerramento: ' + encerramento,
                                   ]})
        # =====================================================================
        # Conteúdo Multimídia
        if self.object.url_audio:
            context.update({'multimidia_audio':
                            'Audio: ' + str(self.object.url_audio)})
        else:
            context.update({'multimidia_audio': 'Audio: Indisponivel'})

        if self.object.url_video:
            context.update({'multimidia_video':
                            'Video: ' + str(self.object.url_video)})
        else:
            context.update({'multimidia_video': 'Video: Indisponivel'})

        # =====================================================================
        # Mesa Diretora
        mesa = IntegranteMesa.objects.filter(
            sessao_plenaria=self.object)

        integrantes = []
        for m in mesa:
            parlamentar = Parlamentar.objects.get(
                id=m.parlamentar_id)
            cargo = CargoMesa.objects.get(
                id=m.cargo_id)
            integrante = {'parlamentar': parlamentar, 'cargo': cargo}
            integrantes.append(integrante)

        context.update({'mesa': integrantes})

        # =====================================================================
        # Presença Sessão
        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id
        )

        parlamentares_sessao = []
        for p in presencas:
            parlamentar = Parlamentar.objects.get(
                id=p.parlamentar_id)
            parlamentares_sessao.append(parlamentar)

        context.update({'presenca_sessao': parlamentares_sessao})

        # =====================================================================
        # Expedientes
        expediente = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id)

        expedientes = []
        for e in expediente:
            tipo = TipoExpediente.objects.get(
                id=e.tipo_id)
            conteudo = sub(
                '&nbsp;', ' ', strip_tags(e.conteudo))

            ex = {'tipo': tipo, 'conteudo': conteudo}
            expedientes.append(ex)

        context.update({'expedientes': expedientes})

        # =====================================================================
        # Matérias Expediente
        materias = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_expediente = []
        for m in materias:
            ementa = m.observacao
            titulo = m.materia
            numero = m.numero_ordem

            if m.resultado:
                resultado = m.resultado
            else:
                resultado = 'Matéria não votada'

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_expediente.append(mat)

        context.update({'materia_expediente': materias_expediente})

        # =====================================================================
        # Oradores Expediente
        oradores = []
        for orador in OradorExpediente.objects.filter(
                sessao_plenaria_id=self.object.id):
            numero_ordem = orador.numero_ordem
            url_discurso = orador.url_discurso
            parlamentar = Parlamentar.objects.get(
                id=orador.parlamentar_id)
            ora = {'numero_ordem': numero_ordem,
                   'url_discurso': url_discurso,
                   'parlamentar': parlamentar
                   }
            oradores.append(ora)

        context.update({'oradores': oradores})

        # =====================================================================
        # Presença Ordem do Dia
        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )

        parlamentares_ordem = []
        for p in presencas:
            parlamentar = Parlamentar.objects.get(
                id=p.parlamentar_id)
            parlamentares_ordem.append(parlamentar)

        context.update({'presenca_ordem': parlamentares_ordem})

        # =====================================================================
        # Matérias Ordem do Dia
        ordem = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            # Verificar resultado
            if o.resultado:
                resultado = o.resultado
            else:
                resultado = 'Matéria não votada'

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)


class ExpedienteForm(forms.Form):
    conteudo = forms.CharField(required=False, widget=forms.Textarea)


class ExpedienteView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/expediente.html'
    form_class = ExpedienteForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ExpedienteForm(request.POST)

        if form.is_valid():
            list_tipo = request.POST.getlist('tipo')
            list_conteudo = request.POST.getlist('conteudo')

            for tipo, conteudo in zip(list_tipo, list_conteudo):
                try:
                    ExpedienteSessao.objects.get(
                        sessao_plenaria_id=self.object.id,
                        tipo_id=tipo
                    ).delete()
                except:
                    pass

                expediente = ExpedienteSessao()
                expediente.sessao_plenaria_id = self.object.id
                expediente.tipo_id = tipo
                expediente.conteudo = conteudo
                expediente.save()
            return self.form_valid(form)
        else:
            return self.form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        tipos = TipoExpediente.objects.all()
        expedientes_sessao = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id)

        expedientes_salvos = []
        for e in expedientes_sessao:
            expedientes_salvos.append(e.tipo)

        tipos_null = list(set(tipos) - set(expedientes_salvos))

        expedientes = []
        for e, t in zip(expedientes_sessao, tipos):
            expedientes.append({'tipo': e.tipo,
                                'conteudo': e.conteudo
                                })
        context.update({'expedientes': expedientes})

        for e in tipos_null:
            expedientes.append({'tipo': e,
                                'conteudo': ''
                                })

        context.update({'expedientes': expedientes})
        return self.render_to_response(context)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expediente', kwargs={'pk': pk})


class ExplicacaoView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/explicacao.html'
    form_class = OradorForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OradorForm(request.POST)

        if 'adicionar' in request.POST:
            if form.is_valid():
                orador = Orador()
                orador.sessao_plenaria_id = self.object.id
                orador.numero_ordem = request.POST['numero_ordem']
                orador.parlamentar = Parlamentar.objects.get(
                    id=request.POST['parlamentar'])
                orador.url_discurso = request.POST['url_discurso']
                orador.save()
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        elif 'reordenar' in request.POST:
            orador = Orador.objects.filter(
                sessao_plenaria_id=self.object.id)
            ordem_num = 1
            for o in orador:
                o.numero_ordem = ordem_num
                o.save()
                ordem_num += 1
            return self.get(self, request, args, kwargs)

    def get_candidatos_orador(self):
        self.object = self.get_object()
        lista_parlamentares = []
        lista_oradores = []

        for parlamentar in Parlamentar.objects.all():
            if parlamentar.ativo:
                lista_parlamentares.append(parlamentar)

        for orador in Orador.objects.filter(
                sessao_plenaria_id=self.object.id):
            parlamentar = Parlamentar.objects.get(
                id=orador.parlamentar_id)
            lista_oradores.append(parlamentar)

        lista = list(set(lista_parlamentares) - set(lista_oradores))
        lista.sort(key=lambda x: x.nome_parlamentar)
        return lista

    def get_oradores(self):
        self.object = self.get_object()

        for orador in Orador.objects.filter(
                sessao_plenaria_id=self.object.id).order_by('numero_ordem'):
            numero_ordem = orador.numero_ordem
            url_discurso = orador.url_discurso
            parlamentar = Parlamentar.objects.get(
                id=orador.parlamentar_id)
            yield(numero_ordem, url_discurso, parlamentar)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:explicacao', kwargs={'pk': pk})


class ExplicacaoDelete(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/delete_explicacao.html'
    form_class = OradorDeleteForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        oid = kwargs['oid']
        form = OradorDeleteForm(request.POST)

        if form.is_valid():
            orador = Orador.objects.get(
                sessao_plenaria_id=self.object.id,
                parlamentar_id=oid)
            orador.delete()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:explicacao', kwargs={'pk': pk})


class ExplicacaoEdit(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/edit_explicacao.html'
    form_class = OradorForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = OradorForm(request.POST)

        pk = kwargs['pk']
        oid = kwargs['oid']

        if form.is_valid():
            orador = Orador.objects.get(
                sessao_plenaria_id=pk,
                parlamentar_id=oid)
            orador.delete()

            orador = Orador()
            orador.sessao_plenaria_id = pk
            orador.numero_ordem = request.POST['numero_ordem']
            orador.parlamentar = Parlamentar.objects.get(
                id=oid)
            orador.url_discurso = request.POST['url_discurso']
            orador.save()

            return self.form_valid(form)
        else:
            context = self.get_context_data(object=self.object)

            parlamentar = Parlamentar.objects.get(id=oid)
            orador = Orador.objects.get(
                sessao_plenaria=self.object, parlamentar=parlamentar)

            explicacao = {'parlamentar': parlamentar,
                          'url_discurso': orador.url_discurso}
            context.update({'explicacao': explicacao})
            context.update({'form': form})
            return self.render_to_response(context)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        oid = kwargs['oid']

        parlamentar = Parlamentar.objects.get(id=oid)
        orador = Orador.objects.get(
            sessao_plenaria=self.object, parlamentar=parlamentar)

        explicacao = {'parlamentar': parlamentar, 'numero_ordem':
                      orador.numero_ordem, 'url_discurso': orador.url_discurso}
        context.update({'explicacao': explicacao})

        return self.render_to_response(context)

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:explicacao', kwargs={'pk': pk})


class VotacaoForm(forms.Form):
    votos_sim = forms.CharField(required=True, label='Sim')
    votos_nao = forms.CharField(required=True, label='Não')
    abstencoes = forms.CharField(required=True, label='Abstenções')
    total_votos = forms.CharField(required=False, label='total')


class VotacaoEdit(forms.Form):
    pass


class VotacaoEditView(FormMixin, sessao_crud.CrudDetailView):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao_edit.html'

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = VotacaoEdit(request.POST)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            RegistroVotacao.objects.get(
                materia_id=materia_id,
                ordem_id=ordem_id).delete()

            ordem = OrdemDia.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            ordem.votacao_aberta = False
            ordem.resultado = None
            ordem.save()

        return self.form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        url = request.get_full_path()

        if "votsimb" in url:
            titulo = "Votação Simbólica"
        elif "votsec" in url:
            titulo = "Votação Secreta"
        else:
            titulo = "Não definida"

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        ordem = OrdemDia.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            ordem_id=ordem_id)
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente})

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:materiaordemdia_list',
                       kwargs={'pk': pk})


class VotacaoView(FormMixin, sessao_crud.CrudDetailView):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # TODO: HACK, VERIFICAR MELHOR FORMA DE FAZER ISSO
        if "votsimb" in url:
            titulo = "Votação Simbólica"
        elif "votsec" in url:
            titulo = "Votação Secreta"
        else:
            titulo = "Não definida"

        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)
        qtde_presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoForm(request.POST)
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # ====================================================
        if "votsimb" in url:
            titulo = "Votação Simbólica"
        elif "votsec" in url:
            titulo = "Votação Secreta"
        else:
            titulo = "Não definida"

        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)
        qtde_presentes = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})
        context.update({'form': form})
        # ====================================================

        if 'cancelar-votacao' in request.POST:
            ordem.votacao_aberta = False
            ordem.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            ordem_id = kwargs['mid']

            qtde_presentes = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.object.id).count()
            qtde_votos = (int(request.POST['votos_sim']) +
                          int(request.POST['votos_nao']) +
                          int(request.POST['abstencoes']))

            if (int(request.POST['voto_presidente']) == 0):
                qtde_presentes -= 1

            if (qtde_votos > qtde_presentes or qtde_votos < qtde_presentes):
                form._errors["total_votos"] = ErrorList([u""])
                return self.render_to_response(context)
            elif (qtde_presentes == qtde_votos):
                try:
                    votacao = RegistroVotacao()
                    votacao.numero_votos_sim = int(request.POST['votos_sim'])
                    votacao.numero_votos_nao = int(request.POST['votos_nao'])
                    votacao.numero_abstencoes = int(request.POST['abstencoes'])
                    votacao.observacao = request.POST['observacao']
                    votacao.materia_id = materia_id
                    votacao.ordem_id = ordem_id
                    votacao.tipo_resultado_votacao_id = int(
                        request.POST['resultado_votacao'])
                    votacao.save()
                except:
                    return self.form_invalid(form)
                else:
                    ordem = OrdemDia.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    ordem.resultado = resultado.nome
                    ordem.votacao_aberta = False
                    ordem.save()

                return self.form_valid(form)
        else:
            return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:materiaordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalForm(forms.Form):
    pass


class VotacaoNominalView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/votacao/nominal.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        ordem_id = kwargs['mid']

        ordem = OrdemDia.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ordem.observacao))}
        context.update({'materia': materia})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        ordem_id = kwargs['mid']
        ordem = OrdemDia.objects.get(id=ordem_id)

        form = VotacaoNominalForm(request.POST)

        if 'cancelar-votacao' in request.POST:
            ordem.votacao_aberta = False
            ordem.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            ordem_id = kwargs['mid']

            votos_sim = 0
            votos_nao = 0
            abstencoes = 0
            nao_votou = 0

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if(voto == 'sim'):
                    votos_sim += 1
                elif(voto == 'nao'):
                    votos_nao += 1
                elif(voto == 'abstencao'):
                    abstencoes += 1
                elif(voto == 'nao_votou'):
                    nao_votou += 1

            try:
                votacao = RegistroVotacao()
                votacao.numero_votos_sim = votos_sim
                votacao.numero_votos_nao = votos_nao
                votacao.numero_abstencoes = abstencoes
                votacao.observacao = request.POST['observacao']
                votacao.materia_id = materia_id
                votacao.ordem_id = ordem_id
                votacao.tipo_resultado_votacao_id = int(
                    request.POST['resultado_votacao'])
                votacao.save()
            except:
                return self.form_invalid(form)
            else:
                votacao = RegistroVotacao.objects.get(
                    materia_id=materia_id,
                    ordem_id=ordem_id)

                for votos in request.POST.getlist('voto_parlamentar'):
                    v = votos.split(':')
                    voto = v[0]
                    parlamentar_id = v[1]

                    voto_parlamentar = VotoParlamentar()
                    if(voto == 'sim'):
                        voto_parlamentar.voto = 'Sim'
                    elif(voto == 'nao'):
                        voto_parlamentar.voto = 'Não'
                    elif(voto == 'abstencao'):
                        voto_parlamentar.voto = 'Abstenção'
                    elif(voto == 'nao_votou'):
                        voto_parlamentar.voto = 'Não Votou'
                    voto_parlamentar.parlamentar_id = parlamentar_id
                    voto_parlamentar.votacao_id = votacao.id
                    voto_parlamentar.save()

                    ordem = OrdemDia.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    ordem.resultado = resultado.nome
                    ordem.votacao_aberta = False
                    ordem.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield parlamentar

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:materiaordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalEditView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/votacao/nominal_edit.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            ordem_id=ordem_id)
        ordem = OrdemDia.objects.get(id=ordem_id)
        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': ordem.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ordem.observacao))}
        context.update({'materia': materia})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoEdit(request.POST)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            registro = RegistroVotacao.objects.get(
                materia_id=materia_id,
                ordem_id=ordem_id)

            ordem = OrdemDia.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            ordem.resultado = None
            ordem.votacao_aberta = False
            ordem.save()

            try:
                votacao = VotoParlamentar.objects.filter(
                    votacao_id=registro.id)
                for v in votacao:
                    v.delete()
            except:
                pass

            registro.delete()

        return self.form_valid(form)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:materiaordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalExpedienteView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/votacao/nominal.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        ordem_id = kwargs['mid']

        expediente = ExpedienteMateria.objects.get(id=ordem_id)

        materia = {'materia': expediente.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(expediente.observacao))}
        context.update({'materia': materia})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        ordem_id = kwargs['mid']
        expediente = ExpedienteMateria.objects.get(id=ordem_id)

        form = VotacaoNominalForm(request.POST)

        if 'cancelar-votacao' in request.POST:
            expediente.votacao_aberta = False
            expediente.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            ordem_id = kwargs['mid']

            votos_sim = 0
            votos_nao = 0
            abstencoes = 0
            nao_votou = 0

            for votos in request.POST.getlist('voto_parlamentar'):
                v = votos.split(':')
                voto = v[0]
                parlamentar_id = v[1]

                if(voto == 'sim'):
                    votos_sim += 1
                elif(voto == 'nao'):
                    votos_nao += 1
                elif(voto == 'abstencao'):
                    abstencoes += 1
                elif(voto == 'nao_votou'):
                    nao_votou += 1

            try:
                votacao = RegistroVotacao()
                votacao.numero_votos_sim = votos_sim
                votacao.numero_votos_nao = votos_nao
                votacao.numero_abstencoes = abstencoes
                votacao.observacao = request.POST['observacao']
                votacao.materia_id = materia_id
                votacao.ordem_id = ordem_id
                votacao.tipo_resultado_votacao_id = int(
                    request.POST['resultado_votacao'])
                votacao.save()
            except:
                return self.form_invalid(form)
            else:
                votacao = RegistroVotacao.objects.get(
                    materia_id=materia_id,
                    ordem_id=ordem_id)

                for votos in request.POST.getlist('voto_parlamentar'):
                    v = votos.split(':')
                    voto = v[0]
                    parlamentar_id = v[1]

                    voto_parlamentar = VotoParlamentar()
                    if(voto == 'sim'):
                        voto_parlamentar.voto = 'Sim'
                    elif(voto == 'nao'):
                        voto_parlamentar.voto = 'Não'
                    elif(voto == 'abstencao'):
                        voto_parlamentar.voto = 'Abstenção'
                    elif(voto == 'nao_votou'):
                        voto_parlamentar.voto = 'Não Votou'
                    voto_parlamentar.parlamentar_id = parlamentar_id
                    voto_parlamentar.votacao_id = votacao.id
                    voto_parlamentar.save()

                    ordem = ExpedienteMateria.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    ordem.resultado = resultado.nome
                    ordem.votacao_aberta = False
                    ordem.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id
        )
        presentes = [p.parlamentar for p in presencas]

        for parlamentar in Parlamentar.objects.filter(ativo=True):
            if parlamentar in presentes:
                yield parlamentar

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expedienteordemdia_list',
                       kwargs={'pk': pk})


class VotacaoNominalExpedienteEditView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/votacao/nominal_edit.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            ordem_id=ordem_id)
        ordem = ExpedienteMateria.objects.get(id=ordem_id)
        votos = VotoParlamentar.objects.filter(votacao_id=votacao.id)

        list_votos = []
        for v in votos:
            parlamentar = Parlamentar.objects.get(id=v.parlamentar_id)
            list_votos.append({'parlamentar': parlamentar, 'voto': v.voto})

        context.update({'votos': list_votos})

        materia = {'materia': ordem.materia,
                   'ementa': sub(
                       '&nbsp;', ' ', strip_tags(ordem.observacao))}
        context.update({'materia': materia})

        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao': votacao_existente})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoEdit(request.POST)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            registro = RegistroVotacao.objects.get(
                materia_id=materia_id,
                ordem_id=ordem_id)

            ordem = ExpedienteMateria.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            ordem.resultado = None
            ordem.votacao_aberta = False
            ordem.save()

            try:
                votacao = VotoParlamentar.objects.filter(
                    votacao_id=registro.id)
                for v in votacao:
                    v.delete()
            except:
                pass

            registro.delete()

        return self.form_valid(form)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expedienteordemdia_list',
                       kwargs={'pk': pk})


class VotacaoExpedienteView(FormMixin, sessao_crud.CrudDetailView):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # TODO: HACK, VERIFICAR MELHOR FORMA DE FAZER ISSO
        if "votsimb" in url:
            titulo = "Votação Simbólica"
        elif "votsec" in url:
            titulo = "Votação Secreta"
        else:
            titulo = "Não definida"

        ordem_id = kwargs['mid']
        ordem = ExpedienteMateria.objects.get(id=ordem_id)
        qtde_presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = VotacaoForm(request.POST)
        context = self.get_context_data(object=self.object)
        url = request.get_full_path()

        # ====================================================
        if "votsimb" in url:
            titulo = "Votação Simbólica"
        elif "votsec" in url:
            titulo = "Votação Secreta"
        else:
            titulo = "Não definida"

        ordem_id = kwargs['mid']
        ordem = ExpedienteMateria.objects.get(id=ordem_id)
        qtde_presentes = SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria_id=self.object.id).count()

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'votacao_titulo': titulo,
                        'materia': materia,
                        'total_presentes': qtde_presentes})
        context.update({'form': form})
        # ====================================================

        if 'cancelar-votacao' in request.POST:
            ordem.votacao_aberta = False
            ordem.save()
            return self.form_valid(form)

        if form.is_valid():
            materia_id = kwargs['oid']
            ordem_id = kwargs['mid']

            qtde_presentes = SessaoPlenariaPresenca.objects.filter(
                sessao_plenaria_id=self.object.id).count()
            qtde_votos = (int(request.POST['votos_sim']) +
                          int(request.POST['votos_nao']) +
                          int(request.POST['abstencoes']))

            if (int(request.POST['voto_presidente']) == 0):
                qtde_presentes -= 1

            if (qtde_votos > qtde_presentes or qtde_votos < qtde_presentes):
                form._errors["total_votos"] = ErrorList([u""])
                return self.render_to_response(context)
            elif (qtde_presentes == qtde_votos):
                try:
                    votacao = RegistroVotacao()
                    votacao.numero_votos_sim = int(request.POST['votos_sim'])
                    votacao.numero_votos_nao = int(request.POST['votos_nao'])
                    votacao.numero_abstencoes = int(request.POST['abstencoes'])
                    votacao.observacao = request.POST['observacao']
                    votacao.materia_id = materia_id
                    votacao.ordem_id = ordem_id
                    votacao.tipo_resultado_votacao_id = int(
                        request.POST['resultado_votacao'])
                    votacao.save()
                except:
                    return self.form_invalid(form)
                else:
                    ordem = ExpedienteMateria.objects.get(
                        sessao_plenaria_id=self.object.id,
                        materia_id=materia_id)
                    resultado = TipoResultadoVotacao.objects.get(
                        id=request.POST['resultado_votacao'])
                    ordem.resultado = resultado.nome
                    ordem.votacao_aberta = False
                    ordem.save()

                return self.form_valid(form)
        else:
            return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expedienteordemdia_list',
                       kwargs={'pk': pk})


class VotacaoExpedienteEditView(FormMixin, sessao_crud.CrudDetailView):

    '''
        Votação Simbólica e Secreta
    '''

    template_name = 'sessao/votacao/votacao_edit.html'

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()
        form = VotacaoEdit(request.POST)

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        if(int(request.POST['anular_votacao']) == 1):
            RegistroVotacao.objects.get(
                materia_id=materia_id,
                ordem_id=ordem_id).delete()

            ordem = ExpedienteMateria.objects.get(
                sessao_plenaria_id=self.object.id,
                materia_id=materia_id)
            ordem.votacao_aberta = False
            ordem.resultado = None
            ordem.save()

        return self.form_valid(form)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        url = request.get_full_path()

        if "votsimb" in url:
            titulo = "Votação Simbólica"
        elif "votsec" in url:
            titulo = "Votação Secreta"
        else:
            titulo = "Não definida"

        materia_id = kwargs['oid']
        ordem_id = kwargs['mid']

        ordem = ExpedienteMateria.objects.get(id=ordem_id)

        materia = {'materia': ordem.materia, 'ementa': ordem.observacao}
        context.update({'materia': materia})

        votacao = RegistroVotacao.objects.get(
            materia_id=materia_id,
            ordem_id=ordem_id)
        votacao_existente = {'observacao': sub(
            '&nbsp;', ' ', strip_tags(votacao.observacao)),
            'tipo_resultado':
            votacao.tipo_resultado_votacao_id}
        context.update({'votacao_titulo': titulo,
                        'votacao': votacao_existente})

        return self.render_to_response(context)

    def get_tipos_votacao(self):
        for tipo in TipoResultadoVotacao.objects.all():
            yield tipo

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('sessaoplenaria:expedienteordemdia_list',
                       kwargs={'pk': pk})


class SessaoListView(ListView):
    template_name = "sessao/sessao_list.html"
    paginate_by = 10
    model = SessaoPlenaria

    def get_queryset(self):
        return SessaoPlenaria.objects.all().order_by('-data_inicio')

    def get_context_data(self, **kwargs):
        context = super(SessaoListView, self).get_context_data(**kwargs)

        paginator = context['paginator']
        page_obj = context['page_obj']

        context['page_range'] = sapl.crud.make_pagination(
                page_obj.number, paginator.num_pages)
        return context


class PautaSessaoListView(SessaoListView):
    template_name = "sessao/pauta_sessao_list.html"


class PautaSessaoDetailView(sessao_crud.CrudDetailView):
    template_name = "sessao/pauta_sessao_detail.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        # =====================================================================
        # Identificação Básica
        abertura = self.object.data_inicio.strftime('%d/%m/%Y')
        encerramento = self.object.data_fim.strftime('%d/%m/%Y')

        context.update({'basica': ['Tipo de Sessão: ' + str(self.object.tipo),
                                   'Abertura: ' + abertura,
                                   'Encerramento: ' + encerramento,
                                   ]})
        # =====================================================================
        # Matérias Expediente
        materias = ExpedienteMateria.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_expediente = []
        for m in materias:
            ementa = m.observacao
            titulo = m.materia
            numero = m.numero_ordem

            if m.resultado:
                resultado = m.resultado
            else:
                resultado = 'Matéria não votada'

            autoria = Autoria.objects.filter(materia_id=m.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_expediente.append(mat)

        context.update({'materia_expediente': materias_expediente})
        # =====================================================================
        # Expedientes
        expediente = ExpedienteSessao.objects.filter(
            sessao_plenaria_id=self.object.id)

        expedientes = []
        for e in expediente:
            tipo = TipoExpediente.objects.get(
                id=e.tipo_id)
            conteudo = sub(
                '&nbsp;', ' ', strip_tags(e.conteudo))

            ex = {'tipo': tipo, 'conteudo': conteudo}
            expedientes.append(ex)

        context.update({'expedientes': expedientes})
        # =====================================================================
        # Matérias Ordem do Dia
        ordem = OrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id)

        materias_ordem = []
        for o in ordem:
            ementa = o.observacao
            titulo = o.materia
            numero = o.numero_ordem

            # Verificar resultado
            if o.resultado:
                resultado = o.resultado
            else:
                resultado = 'Matéria não votada'

            autoria = Autoria.objects.filter(
                materia_id=o.materia_id)
            autor = [str(x.autor) for x in autoria]

            mat = {'ementa': ementa,
                   'titulo': titulo,
                   'numero': numero,
                   'resultado': resultado,
                   'autor': autor
                   }
            materias_ordem.append(mat)

        context.update({'materias_ordem': materias_ordem})

        return self.render_to_response(context)
