from django.utils.translation import ugettext_lazy as _

from braces.views import FormMessagesMixin
from django.core.urlresolvers import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView, DetailView)

from sapl.crud import build_crud
from .models import (TipoSessaoPlenaria, SessaoPlenaria,
                     ExpedienteMateria, OrdemDia, TipoResultadoVotacao,
                     RegistroVotacao, TipoExpediente)


tipo_sessao_crud = build_crud(
    TipoSessaoPlenaria,

    [_('Tipo de Sessão Plenária'),
     [('nome', 6), ('quorum_minimo', 6)]],
)

sessao_crud = build_crud(
    SessaoPlenaria,

    [_('Dados Básicos'),
     [('numero', 3),
      ('tipo', 3),
      ('legislatura', 3),
      ('sessao_legislativa', 3)],
     [('data_inicio', 12)],
     [('data_fim', 12)],
     [('dia', 2),
      ('hora_inicio', 2),
      ('hora_fim', 2),
      ('tipo_expediente', 6)],
     [('url_audio', 6), ('url_video', 6)]],
)

expediente_materia_crud = build_crud(
    ExpedienteMateria,

    [_('Cadastro de Matérias do Expediente'),
     [('data_ordem', 4), ('tip_sessao_FIXME', 4), ('numero_ordem', 4)],
     [('tip_id_basica_FIXME', 4),
      ('num_ident_basica_FIXME', 4),
      ('ano_ident_basica_FIXME', 4)],
     [('tipo_votacao', 12)],
     [('observacao', 12)]],
)

ordem_dia_crud = build_crud(
    OrdemDia,

    [_('Cadastro de Matérias da Ordem do Dia'),
     [('data_ordem', 4), ('tip_sessao_FIXME', 4), ('numero_ordem', 4)],
     [('tip_id_basica_FIXME', 4),
      ('num_ident_basica_FIXME', 4),
      ('ano_ident_basica_FIXME', 4)],
     [('tipo_votacao', 12)],
     [('observacao', 12)]],
)

tipo_resultado_votacao_crud = build_crud(
    TipoResultadoVotacao,

    [_('Tipo de Resultado da Votação'),
     [('nome', 12)]],
)

tipo_expediente_crud = build_crud(
    TipoExpediente,

    [_('Tipo de Expediente'),
     [('nome', 12)]],
)

registro_votacao_crud = build_crud(
    RegistroVotacao,

    [_('Votação Simbólica'),
     [('numero_votos_sim', 3),
      ('numero_votos_nao', 3),
      ('numero_abstencoes', 3),
      ('nao_votou_FIXME', 3)],
     [('votacao_branco_FIXME', 6),
      ('ind_votacao_presidente_FIXME', 6)],
     [('tipo_resultado_votacao', 12)],
     [('observacao', 12)]],
)


class SessaoPlenariaListView(ListView):
    model = SessaoPlenaria


class SessaoPlenariaDetailView(DetailView):
    model = SessaoPlenaria


class SessaoPlenariaCreateView(CreateView):
    model = SessaoPlenaria
    # fields = [f.name for f in SessaoPlenaria._meta.fields]
    form_invalid_message = u"Something went wrong, post was not saved"

    success_url = reverse_lazy('sessao_list')


class SessaoPlenariaUpdateView(FormMessagesMixin, UpdateView):
    model = SessaoPlenaria
    fields = [f.name for f in SessaoPlenaria._meta.fields]

    success_url = reverse_lazy('sessao_list')

    form_invalid_message = u"Something went wrong, post was not saved"

    def get_form_valid_message(self):
        return u"{0} updated successfully!".format(self.object)


class SessaoPlenariaDeleteView(DeleteView):
    model = SessaoPlenaria
    success_url = reverse_lazy('sessao_list')
