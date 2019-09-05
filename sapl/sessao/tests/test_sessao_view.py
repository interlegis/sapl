import pytest
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from model_mommy import mommy

from sapl.parlamentares.models import Legislatura, SessaoLegislativa
from sapl.sessao.models import (SessaoPlenaria, TipoSessaoPlenaria,
                                 IntegranteMesa, SessaoPlenariaPresenca,
                                 JustificativaAusencia, ExpedienteSessao,
                                 TipoExpediente, ExpedienteMateria,
                                 Orador, OcorrenciaSessao)

from sapl.parlamentares.models import Parlamentar, CargoMesa, Filiacao

from sapl.sessao.views import (get_identificacao_basica, get_conteudo_multimidia,
                                get_mesa_diretora, get_presenca_sessao, 
                                get_expedientes, get_materias_expediente,
                                get_oradores_expediente, get_presenca_ordem_do_dia,
                                get_materias_ordem_do_dia, get_oradores_explicacoes_pessoais,
                                get_ocorrencias_da_sessao
                                )


@pytest.mark.django_db(transaction=False)
def test_incluir_sessao_plenaria_submit(admin_client):
    legislatura = mommy.make(Legislatura)
    sessao = mommy.make(SessaoLegislativa)
    tipo = mommy.make(TipoSessaoPlenaria, id=1)

    response = admin_client.post(reverse('sapl.sessao:sessaoplenaria_create'),
                                 {'legislatura': str(legislatura.pk),
                                  'numero': '1',
                                  'tipo': str(tipo.pk),
                                  'sessao_legislativa': str(sessao.pk),
                                  'data_inicio': str(sessao.data_inicio),
                                  'hora_inicio': '10:10'
                                  }, follow=True)

    assert response.status_code == 200

    sessao_plenaria = SessaoPlenaria.objects.first()
    assert sessao_plenaria.tipo == tipo


@pytest.mark.django_db(transaction=False)
def test_incluir_sessao_errors(admin_client):

    response = admin_client.post(reverse('sapl.sessao:sessaoplenaria_create'),
                                 {'salvar': 'salvar'},
                                 follow=True)

    assert (response.context_data['form'].errors['legislatura'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['sessao_legislativa'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['tipo'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['numero'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['data_inicio'] ==
            [_('Este campo é obrigatório.')])
    assert (response.context_data['form'].errors['hora_inicio'] ==
            [_('Este campo é obrigatório.')])

@pytest.mark.django_db(transaction=False)
class TestResumoView():
    def setup(self):
        self.sessao_plenaria = mommy.make(SessaoPlenaria)
        self.parlamentar = mommy.make(Parlamentar)
        self.cargo_mesa = mommy.make(CargoMesa)

        self.integrante_mesa = IntegranteMesa(sessao_plenaria=self.sessao_plenaria,
                                                parlamentar=self.parlamentar,
                                                cargo=self.cargo_mesa)
        self.integrante_mesa.save()

    def test_get_identificacao_basica(self):
        id_basica = get_identificacao_basica(self.sessao_plenaria)
        info_basica = id_basica['basica']
        assert info_basica[0] == 'Tipo de Sessão: ' + str(self.sessao_plenaria.tipo)
        
        data_inicio = self.sessao_plenaria.data_inicio
        abertura = data_inicio.strftime('%d/%m/%Y') if data_inicio else ''
        assert info_basica[1] == 'Abertura: ' + abertura +' - '+ self.sessao_plenaria.hora_inicio
        
        data_fim = self.sessao_plenaria.data_fim
        encerramento = data_fim.strftime('%d/%m/%Y') + ' -' if data_fim else ''
        assert info_basica[2] == 'Encerramento: ' + encerramento +' '+ self.sessao_plenaria.hora_fim

    def test_get_conteudo_multimidia(self):
        multimidia = get_conteudo_multimidia(self.sessao_plenaria)
        url_audio = _('Audio: Indisponível')
        multimidia_video = _('Video: Indisponível')

        if self.sessao_plenaria.url_audio:
            url_audio = _('Audio: ') + str(sessao_plenaria.url_audio)
        if self.sessao_plenaria.url_video:
            multimidia_video = _('Video: ') + str(sessao_plenaria.url_video)

        assert multimidia == {'multimidia_audio':url_audio,
                                'multimidia_video':multimidia_video}

    def test_get_mesa_diretora(self):
        mesa = get_mesa_diretora(self.sessao_plenaria)
        assert mesa == {'mesa':[{ 
            'cargo': self.cargo_mesa,
            'parlamentar': self.parlamentar
        }]}
        
    def test_get_presenca_sessao(self):
        justificativa = mommy.make(JustificativaAusencia,sessao_plenaria=self.sessao_plenaria)
        presenca = mommy.make(SessaoPlenariaPresenca,sessao_plenaria=self.sessao_plenaria)

        resposta_presenca = get_presenca_sessao(self.sessao_plenaria)
        assert resposta_presenca['presenca_sessao'] == [presenca.parlamentar]
        assert resposta_presenca['justificativa_ausencia'][0] == justificativa
    
    def test_get_expedientes(self):
        tipo_expediente = mommy.make(TipoExpediente)
        expediente = mommy.make(ExpedienteSessao,sessao_plenaria=self.sessao_plenaria,tipo=tipo_expediente)

        resposta_expediente = get_expedientes(self.sessao_plenaria)

        assert resposta_expediente['expedientes'] == [{
                'conteudo': expediente.conteudo,
                'tipo': tipo_expediente  
        }]

    def test_get_materias_expediente(self):
        pass

    def test_get_oradores_explicacoes_pessoais(self):
        parlamentar = mommy.make(Parlamentar)
        partido_sigla = mommy.make(Filiacao, parlamentar=parlamentar)
        orador = mommy.make(Orador,sessao_plenaria=self.sessao_plenaria,parlamentar=parlamentar)

        resultado_get_oradores = get_oradores_explicacoes_pessoais(self.sessao_plenaria)

        assert resultado_get_oradores['oradores_explicacoes'] == [{
                'numero_ordem': orador.numero_ordem,
                'parlamentar': parlamentar,
                'sgl_partido': partido_sigla.partido.sigla
        }]

    def test_get_ocorrencias_da_sessao(self):
        ocorrencia = mommy.make(OcorrenciaSessao, sessao_plenaria=self.sessao_plenaria)
        resultado_get_ocorrencia = get_ocorrencias_da_sessao(self.sessao_plenaria)

        assert resultado_get_ocorrencia['ocorrencias_da_sessao'][0] == ocorrencia