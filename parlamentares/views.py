import os

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import CreateView, FormView

from crud import Crud

from .forms import (DependenteEditForm, DependenteForm, FiliacaoEditForm,
                    FiliacaoForm, MandatoEditForm, MandatoForm,
                    ParlamentaresEditForm, ParlamentaresForm,
                    ParlamentaresListForm)
from .models import (CargoMesa, Coligacao, ComposicaoMesa, Dependente,
                     Filiacao, Legislatura, Mandato, NivelInstrucao,
                     Parlamentar, Partido, SessaoLegislativa, SituacaoMilitar,
                     TipoAfastamento, TipoDependente)

cargo_mesa_crud = Crud(CargoMesa, 'cargo_mesa')
legislatura_crud = Crud(Legislatura, 'tabelas_auxiliares#legislatura')
coligacao_crud = Crud(Coligacao, 'coligacao')
partido_crud = Crud(Partido, 'partidos')
dependente_crud = Crud(Dependente, '')
sessao_legislativa_crud = Crud(SessaoLegislativa, 'sessao_legislativa')
parlamentar_crud = Crud(Parlamentar, '')
filiacao_crud = Crud(Filiacao, '')
mandato_crud = Crud(Mandato, '')
tipo_dependente_crud = Crud(TipoDependente, 'tipo_dependente')
nivel_instrucao_crud = Crud(NivelInstrucao, 'nivel_instrucao')
tipo_afastamento_crud = Crud(TipoAfastamento, 'tipo_afastamento')
tipo_militar_crud = Crud(SituacaoMilitar, 'tipo_situa_militar')


class ParlamentaresView(FormView):
    template_name = "parlamentares/parlamentares_list.html"

    def get(self, request, *args, **kwargs):
        form = ParlamentaresListForm()

        if not Legislatura.objects.all():
            mensagem = _('Cadastre alguma Legislatura antes'
                         ' de cadastrar algum Parlamentar')
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
                partido = _('Sem Registro')

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
                partido = _('Sem Registro')

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


class ParlamentaresCadastroView(FormView):
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
            parlamentar.biografia = form.data['biografia']
            parlamentar.save()

            mandato = Mandato()
            mandato.parlamentar = parlamentar
            mandato.legislatura = Legislatura.objects.get(id=pk)
            mandato.save()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form, 'legislatura_id': pk})


class ParlamentaresEditarView(UpdateView):
    template_name = "parlamentares/parlamentares_cadastro.html"
    form_class = ParlamentaresForm

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

        form = ParlamentaresEditForm(request.POST,
                                     request.FILES,
                                     instance=parlamentar)

        if form.is_valid():
            if 'salvar' in request.POST:
                form.save()
            elif 'excluir' in request.POST:
                Mandato.objects.get(parlamentar=parlamentar).delete()
                parlamentar.delete()
            elif "remover" in request.POST:
                try:
                    os.unlink(parlamentar.fotografia.path)
                except OSError:
                    pass  # Should log this error!!!!!
                parlamentar.fotografia = None
                parlamentar.save()
            return self.form_valid(form)
        else:
            return self.render_to_response({'form': form})


class ParlamentaresDependentesView(FormView):

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


class ParlamentaresDependentesEditView(FormView):
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
            elif 'excluir' in request.POST:
                dependente.delete()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': parlamentar,
                 'legislatura_id': dependente.parlamentar.mandato_set.last(
                 ).legislatura_id})


class MesaDiretoraView(FormView):
    template_name = "mesa_diretora/mesa_diretora.html"

    def get_success_url(self):
        return reverse('mesa_diretora')

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


class FiliacaoView(FormView):
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
                    mensagem = _("Você não pode se filiar a algum partido \
                    sem antes se desfiliar do partido anterior")
                    return self.error_message(
                        parlamentar, form, mensagem, request)

                # Dá erro caso a data de desfiliação seja anterior a de
                # filiação
                if data_desfiliacao and data_desfiliacao < data_filiacao:
                    mensagem = _("A data de filiação não pode ser \
                    anterior à data de desfiliação")
                    return self.error_message(
                        parlamentar, form, mensagem, request)

                # Esse bloco garante que não haverá intersecção entre os
                # períodos de filiação
                todas_filiacoes = candidato_filiado
                for i in range(len(todas_filiacoes)):
                    data_init = todas_filiacoes[i].data
                    data_fim = todas_filiacoes[i].data_desfiliacao
                    if data_filiacao >= data_init and data_filiacao < data_fim:
                        mensagem = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                        return self.error_message(
                            parlamentar, form, mensagem, request)

                    if (data_desfiliacao and
                            data_desfiliacao < data_fim and
                            data_desfiliacao > data_init):

                        mensagem = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
                        return self.error_message(
                            parlamentar, form, mensagem, request)

                    if (data_desfiliacao and
                            data_filiacao <= data_init and
                            data_desfiliacao >= data_fim):
                        mensagem = _("A data de filiação e \
                        desfiliação não podem estar no intervalo \
                        de outro período de filiação")
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


class FiliacaoEditView(FormView):
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

            if 'excluir' in request.POST:
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
                    mensagem = _("A data de filiação não pode \
                    anterior à data de desfiliação")
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

                            mensagem = _("A data de filiação e \
                            desfiliação não podem estar no intervalo \
                            de outro período de filiação")
                            return self.error_message(parlamentar,
                                                      form,
                                                      mensagem,
                                                      request)

                        if (data_desfiliacao and
                                data_desfiliacao < data_fim and
                                data_desfiliacao > data_init):

                            mensagem = _("A data de filiação e \
                            desfiliação não podem estar no intervalo \
                            de outro período de filiação")
                            return self.error_message(parlamentar,
                                                      form,
                                                      mensagem,
                                                      request)
                        if (data_desfiliacao and
                                data_filiacao <= data_init and
                                data_desfiliacao >= data_fim):
                            mensagem = _("A data de filiação e \
                            desfiliação não podem estar no intervalo \
                            de outro período de filiação")
                            return self.error_message(parlamentar,
                                                      form,
                                                      mensagem,
                                                      request)

            if 'salvar' in request.POST:
                filiacao.save()
            elif 'excluir' in request.POST:
                filiacao.delete()
            return self.form_valid(form)

        else:
            return self.render_to_response(
                {'form': form,
                 'object': parlamentar,
                 'legislatura_id': parlamentar.mandato_set.last(
                 ).legislatura_id})


class MandatoView(FormView):
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


class MandatoEditView(FormView):
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
            elif 'excluir' in request.POST:
                mandato.delete()
            return self.form_valid(form)
        else:
            return self.render_to_response(
                {'form': form,
                 'object': parlamentar,
                 'legislatura_id': parlamentar.mandato_set.last(
                 ).legislatura_id})
