from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, FormView, UpdateView

import crud.base
from crud.base import Crud

from .forms import (DependenteEditForm, DependenteForm, FiliacaoEditForm,
                    FiliacaoForm, MandatoEditForm, MandatoForm,
                    ParlamentarCreateForm)
from .models import (CargoMesa, Coligacao, ComposicaoMesa, Dependente,
                     Filiacao, Legislatura, Mandato, NivelInstrucao,
                     Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar,
                     TipoAfastamento, TipoDependente)

CargoMesaCrud = Crud.build(CargoMesa, 'cargo_mesa')
LegislaturaCrud = Crud.build(Legislatura, 'tabelas_auxiliares#legislatura')
ColigacaoCrud = Crud.build(Coligacao, 'coligacao')
PartidoCrud = Crud.build(Partido, 'partidos')
DependenteCrud = Crud.build(Dependente, '')
SessaoLegislativaCrud = Crud.build(SessaoLegislativa, 'sessao_legislativa')
FiliacaoCrud = Crud.build(Filiacao, '')
MandatoCrud = Crud.build(Mandato, '')
TipoDependenteCrud = Crud.build(TipoDependente, 'tipo_dependente')
NivelInstrucaoCrud = Crud.build(NivelInstrucao, 'nivel_instrucao')
TipoAfastamentoCrud = Crud.build(TipoAfastamento, 'tipo_afastamento')
TipoMilitarCrud = Crud.build(SituacaoMilitar, 'tipo_situa_militar')


class ParlamentarCrud(Crud):
    model = Parlamentar
    help_path = ''

    class BaseMixin(crud.base.BaseMixin):
        # TODO: partido...
        list_field_names = ['nome_parlamentar', 'ativo']

    class CreateView(crud.base.CrudCreateView):
        form_class = ParlamentarCreateForm

        @property
        def layout_key(self):
            return 'ParlamentarCreate'


def validate(form, parlamentar, filiacao, request):
    data_filiacao = form.cleaned_data['data']
    data_desfiliacao = form.cleaned_data['data_desfiliacao']

    # Dá erro caso a data de desfiliação seja anterior a de filiação
    if data_desfiliacao and data_desfiliacao < data_filiacao:
        error_msg = _("A data de filiação não pode anterior \
                      à data de desfiliação")
        messages.add_message(request, messages.ERROR, error_msg)
        return False

    # Esse bloco garante que não haverá intersecção entre os
    # períodos de filiação
    id_filiacao_atual = filiacao.pk
    todas_filiacoes = parlamentar.filiacao_set.all()

    for filiacoes in todas_filiacoes:
        if (not filiacoes.data_desfiliacao and
                filiacoes.id != id_filiacao_atual):
            error_msg = _("O parlamentar não pode se filiar a algum partido \
                       sem antes se desfiliar do partido anterior")
            messages.add_message(request, messages.ERROR, error_msg)
            return False

    error_msg = None
    for filiacoes in todas_filiacoes:
        if filiacoes.id != id_filiacao_atual:

            data_init = filiacoes.data
            data_fim = filiacoes.data_desfiliacao

            if data_init <= data_filiacao < data_fim:

                error_msg = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                break

            if (data_desfiliacao and
                    data_init < data_desfiliacao < data_fim):

                error_msg = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                break

            if (data_desfiliacao and
                data_filiacao <= data_init and
                    data_desfiliacao >= data_fim):

                error_msg = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                break

    if error_msg:
        messages.add_message(request, messages.ERROR, error_msg)
        return False
    else:
        return True


class ParlamentaresDependentesView(CreateView):
    template_name = "parlamentares/parlamentares_dependentes.html"
    form_class = DependenteForm
    model = Dependente

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares:parlamentares_dependentes',
                       kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super(ParlamentaresDependentesView, self).\
            get_context_data(**kwargs)
        pk = self.kwargs['pk']
        parlamentar = Parlamentar.objects.get(pk=pk)
        dependentes = Dependente.objects.filter(
            parlamentar=parlamentar).order_by('nome', 'tipo')

        if len(parlamentar.mandato_set.all()) == 0:
            legislatura_id = 0
        else:
            legislatura_id = parlamentar.mandato_set.last().legislatura.id

        context.update({'object': parlamentar,
                        'dependentes': dependentes,
                        # precisa de legislatura_id???
                        'legislatura_id': legislatura_id})
        return context

    def form_valid(self, form):
        parlamentar_id = self.kwargs['pk']
        dependente = form.save(commit=False)
        parlamentar = Parlamentar.objects.get(id=parlamentar_id)
        dependente.parlamentar = parlamentar
        dependente.save()
        return HttpResponseRedirect(self.get_success_url())


class ParlamentaresDependentesEditView(UpdateView):
    template_name = "parlamentares/parlamentares_dependentes_edit.html"
    form_class = DependenteEditForm
    model = Dependente
    pk_url_kwarg = 'dk'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares:parlamentares_dependentes',
                       kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super(ParlamentaresDependentesEditView, self).\
            get_context_data(**kwargs)
        parlamentar = Parlamentar.objects.get(id=self.kwargs['pk'])
        context.update({
            'object': parlamentar,
            'legislatura_id': parlamentar.mandato_set.last(
            ).legislatura_id})
        return context

    def form_valid(self, form):
        if 'salvar' in self.request.POST:
            form.save()
        elif 'excluir' in self.request.POST:
            dependente = form.instance
            dependente.delete()
        return HttpResponseRedirect(self.get_success_url())


class MesaDiretoraView(FormView):
    template_name = "mesa_diretora/mesa_diretora.html"
    success_url = reverse_lazy('parlamentares:mesa_diretora')

    # Essa função avisa quando se pode compor uma Mesa Legislativa)
    def validation(self, request):
        mensagem = _("Não há nenhuma Sessão Legislativa cadastrada. \
        Só é possível compor uma Mesa Diretora quando há uma Sessão \
        Legislativa cadastrada.")
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

            return redirect('parlamentares:mesa_diretora')

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
            return redirect('parlamentares:mesa_diretora')
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


class FiliacaoView(CreateView):
    template_name = "parlamentares/parlamentares_filiacao.html"
    form_class = FiliacaoForm
    model = Filiacao

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares:parlamentares_filiacao',
                       kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super(FiliacaoView, self).get_context_data(**kwargs)
        pid = self.kwargs['pk']
        parlamentar = Parlamentar.objects.get(id=pid)
        filiacoes = Filiacao.objects.filter(parlamentar=parlamentar)

        if len(parlamentar.mandato_set.all()) == 0:
            legislatura_id = 0
        else:
            legislatura_id = parlamentar.mandato_set.last().legislatura.id

        context.update(
            {'object': parlamentar,
             'filiacoes': filiacoes,
             'legislatura_id': legislatura_id})
        return context

    def form_valid(self, form):
        if 'salvar' in self.request.POST:
            filiacao = form.save(commit=False)
            parlamentar = Parlamentar.objects.get(id=self.kwargs['pk'])
            filiacao.parlamentar = parlamentar

            if not validate(form, parlamentar, filiacao, self.request):
                return self.form_invalid(form)

            filiacao.save()
        return HttpResponseRedirect(self.get_success_url())


class FiliacaoEditView(UpdateView):
    template_name = "parlamentares/parlamentares_filiacao_edit.html"
    form_class = FiliacaoEditForm
    model = Filiacao
    pk_url_kwarg = 'dk'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares:parlamentares_filiacao',
                       kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super(FiliacaoEditView, self).get_context_data(**kwargs)
        parlamentar = Parlamentar.objects.get(id=self.kwargs['pk'])
        context.update(
            {'object': parlamentar,
             'legislatura_id': parlamentar.mandato_set.last(
             ).legislatura_id})
        return context

    def form_valid(self, form):
        filiacao = form.save(commit=False)
        if 'excluir' in self.request.POST:
            filiacao.delete()
        elif 'salvar' in self.request.POST:
            parlamentar = Parlamentar.objects.get(id=self.kwargs['pk'])
            filiacao.parlamentar = parlamentar

            if not validate(form, parlamentar, filiacao, self.request):
                return self.form_invalid(form)

            filiacao.save()
        return HttpResponseRedirect(self.get_success_url())


class MandatoView(CreateView):
    template_name = "parlamentares/parlamentares_mandato.html"
    model = Mandato
    form_class = MandatoForm

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares:parlamentares_mandato',
                       kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super(MandatoView, self).get_context_data(**kwargs)
        pid = self.kwargs['pk']
        parlamentar = Parlamentar.objects.get(id=pid)
        mandatos = Mandato.objects.filter(parlamentar=parlamentar)

        if len(parlamentar.mandato_set.all()) == 0:
            legislatura_id = 0
        else:
            legislatura_id = parlamentar.mandato_set.last().legislatura.id

        context.update(
            {'object': parlamentar,
             'mandatos': mandatos,
             'legislatura_id': legislatura_id
             }
        )
        return context

    def form_valid(self, form):
        pid = self.kwargs['pk']
        parlamentar = Parlamentar.objects.get(id=pid)
        mandato = form.save(commit=False)
        mandato.parlamentar = parlamentar
        mandato.save()
        return HttpResponseRedirect(self.get_success_url())


class MandatoEditView(UpdateView):
    template_name = "parlamentares/parlamentares_mandato_edit.html"
    model = Mandato
    form_class = MandatoEditForm
    pk_url_kwarg = 'dk'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse('parlamentares:parlamentares_mandato',
                       kwargs={'pk': pk})

    def get_context_data(self, **kwargs):
        context = super(MandatoEditView, self).get_context_data(**kwargs)
        parlamentar = Parlamentar.objects.get(id=self.kwargs['pk'])
        context.update(
            {'object': parlamentar,
             'legislatura_id': parlamentar.mandato_set.last(
             ).legislatura_id})
        return context

    def form_valid(self, form):
        form = self.get_form()
        parlamentar = Parlamentar.objects.get(id=self.kwargs['pk'])
        if 'salvar' in self.request.POST:
            mandato = form.save(commit=False)
            mandato.parlamentar = parlamentar
            mandato.save()
        elif 'excluir' in self.request.POST:
            form.instance.delete()

        return HttpResponseRedirect(self.get_success_url())
