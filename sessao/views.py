from django import forms
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import FormMixin
from extra_views import InlineFormSetView

from parlamentares.models import Parlamentar
from sapl.crud import build_crud

from .models import (ExpedienteMateria, ExpedienteSessao, OradorExpediente,
                     OrdemDia, PresencaOrdemDia, RegistroVotacao,
                     SessaoPlenaria, SessaoPlenariaPresenca, TipoExpediente,
                     TipoResultadoVotacao, TipoSessaoPlenaria)

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


class ExpedienteView(InlineFormSetView):
    model = SessaoPlenaria
    inline_model = ExpedienteSessao
    template_name = 'sessao/expediente.html'
    fields = ('tipo', 'conteudo')
    can_delete = True
    extra = 1


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
                sessao_plen_id=self.object.id)

            # Id dos parlamentares presentes
            marcados = request.POST.getlist('presenca')

            # Deletar os que foram desmarcadors
            deletar = set(set(presentes_banco) - set(marcados))
            for d in deletar:
                SessaoPlenariaPresenca.objects.filter(
                    parlamentar_id=d.parlamentar_id).delete()

            for p in marcados:
                sessao = SessaoPlenariaPresenca()
                sessao.sessao_plen = self.object
                sessao.parlamentar = Parlamentar.objects.get(id=p)
                sessao.save()

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return self.detail_url

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = SessaoPlenariaPresenca.objects.filter(
            sessao_plen_id=self.object.id
        )

        presentes = []
        for p in presencas:
            presentes.append(p.parlamentar.id)

        for parlamentar in Parlamentar.objects.all():
            if parlamentar.ativo:
                try:
                    presentes.index(parlamentar.id)
                except ValueError:
                    yield (parlamentar, False)
                else:
                    yield (parlamentar, True)


class PainelView(sessao_crud.CrudDetailView):
    template_name = 'sessao/painel.html'


class PresencaOrdemDiaView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/presencaOrdemDia.html'
    form_class = PresencaForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            # Pegar os presentes salvos no banco
            presentes_banco = PresencaOrdemDia.objects.filter(
                sessao_plenaria_id=self.object.id)

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

    def get_success_url(self):
        return self.detail_url

    def get_parlamentares(self):
        self.object = self.get_object()

        presencas = PresencaOrdemDia.objects.filter(
            sessao_plenaria_id=self.object.id
        )

        presentes = []
        for p in presencas:
            presentes.append(p.parlamentar.id)

        for parlamentar in Parlamentar.objects.all():
            if parlamentar.ativo:
                try:
                    presentes.index(parlamentar.id)
                except ValueError:
                    yield (parlamentar, False)
                else:
                    yield (parlamentar, True)


class OradorForm(forms.Form):
    numero_ordem = forms.IntegerField(required=True)
    parlamentar = forms.CharField(required=True, max_length=20)
    url_discurso = forms.CharField(required=False, max_length=100)


class OradorDeleteForm(forms.Form):
    pass


class OradorExpedienteDelete(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/delete_orador.html'
    form_class = OradorDeleteForm

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        current_url = request.get_full_path()
        words = current_url.split('/')
        form = OradorDeleteForm(request.POST)

        if form.is_valid():
            orador = OradorExpediente.objects.get(
                sessao_plenaria_id=self.object.id,
                parlamentar_id=words[-1])
            orador.delete()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return self.detail_url


class OradorExpedienteView(FormMixin, sessao_crud.CrudDetailView):
    template_name = 'sessao/oradorExpediente.html'
    form_class = OradorForm

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        print(request.POST['numero_ordem'], request.POST['parlamentar'])
        form = OradorForm(request.POST)

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

    def get_success_url(self):
        return self.detail_url
