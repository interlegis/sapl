import pytest
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from model_bakery import baker

from sapl.parlamentares.models import Legislatura, SessaoLegislativa
from sapl.sessao.models import (SessaoPlenaria, TipoSessaoPlenaria,
                                 IntegranteMesa, SessaoPlenariaPresenca,
                                 PresencaOrdemDia,
                                 JustificativaAusencia, ExpedienteSessao,
                                 TipoExpediente, ExpedienteMateria,
                                 Orador, OcorrenciaSessao,
                                 restringe_sessoes_visiveis)

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
    legislatura = baker.make(Legislatura)
    sessao = baker.make(SessaoLegislativa)
    tipo = baker.make(TipoSessaoPlenaria, id=1)

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
        self.sessao_plenaria = baker.make(SessaoPlenaria)
        self.parlamentar = baker.make(Parlamentar)
        self.cargo_mesa = baker.make(CargoMesa)

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
        justificativa = baker.make(JustificativaAusencia,sessao_plenaria=self.sessao_plenaria)
        presenca = baker.make(SessaoPlenariaPresenca,sessao_plenaria=self.sessao_plenaria)

        resposta_presenca = get_presenca_sessao(self.sessao_plenaria)
        assert resposta_presenca['presenca_sessao'] == [presenca.parlamentar]
        assert resposta_presenca['justificativa_ausencia'][0] == justificativa
    
    def test_get_expedientes(self):
        tipo_expediente = baker.make(TipoExpediente)
        expediente = baker.make(ExpedienteSessao,sessao_plenaria=self.sessao_plenaria,tipo=tipo_expediente)

        resposta_expediente = get_expedientes(self.sessao_plenaria)

        assert resposta_expediente['expedientes'] == [{
                'conteudo': expediente.conteudo,
                'tipo': tipo_expediente  
        }]

    def test_get_materias_expediente(self):
        pass

    def test_get_oradores_explicacoes_pessoais(self):
        parlamentar = baker.make(Parlamentar)
        partido_sigla = baker.make(Filiacao, parlamentar=parlamentar)
        orador = baker.make(Orador,sessao_plenaria=self.sessao_plenaria,parlamentar=parlamentar)

        resultado_get_oradores = get_oradores_explicacoes_pessoais(self.sessao_plenaria)

        assert resultado_get_oradores['oradores_explicacoes'] == [{
                'numero_ordem': orador.numero_ordem,
                'parlamentar': parlamentar,
                'sgl_partido': partido_sigla.partido.sigla
        }]

    def test_get_ocorrencias_da_sessao(self):
        ocorrencia = baker.make(OcorrenciaSessao, sessao_plenaria=self.sessao_plenaria)
        resultado_get_ocorrencia = get_ocorrencias_da_sessao(self.sessao_plenaria)

        assert resultado_get_ocorrencia['ocorrencias_da_sessao'][0] == ocorrencia


@pytest.mark.django_db(transaction=False)
def test_visiveis_para_oculta_do_anonimo_apenas_a_sessao_previa():
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False)
    com_pauta = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=True)
    iniciada = baker.make(SessaoPlenaria, iniciada=True, publicar_pauta=False)
    # Sessões anteriores à migração 0027 ficaram com `iniciada` em NULL.
    legada = baker.make(SessaoPlenaria, iniciada=None, publicar_pauta=False)

    visiveis = restringe_sessoes_visiveis(
        SessaoPlenaria.objects.all(), AnonymousUser())

    assert previa not in visiveis
    assert com_pauta in visiveis
    assert iniciada in visiveis
    assert legada in visiveis


@pytest.mark.django_db(transaction=False)
def test_visiveis_para_nao_oculta_nada_de_usuario_autenticado():
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False)

    operador = baker.make(get_user_model())

    assert previa in restringe_sessoes_visiveis(
        SessaoPlenaria.objects.all(), operador)


@pytest.mark.django_db(transaction=False)
def test_pesquisar_sessao_nao_lista_sessao_previa_para_anonimo(client):
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False,
                        data_inicio=date(2025, 11, 5))
    iniciada = baker.make(SessaoPlenaria, iniciada=True, publicar_pauta=False,
                          data_inicio=date(2025, 11, 5))

    response = client.get(reverse('sapl.sessao:pesquisar_sessao'),
                          {'data_inicio__year': '2025'})

    assert response.status_code == 200
    assert previa not in response.context['object_list']
    assert iniciada in response.context['object_list']


@pytest.mark.django_db(transaction=False)
def test_pesquisar_sessao_lista_sessao_previa_para_autenticado(admin_client):
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False,
                        data_inicio=date(2025, 11, 5))

    response = admin_client.get(reverse('sapl.sessao:pesquisar_sessao'),
                                {'data_inicio__year': '2025'})

    assert response.status_code == 200
    assert previa in response.context['object_list']


@pytest.mark.django_db(transaction=False)
def test_detail_sessao_previa_indisponivel_para_anonimo(client):
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False)

    response = client.get(reverse('sapl.sessao:sessaoplenaria_detail',
                                  kwargs={'pk': previa.pk}))

    assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
def test_resumo_de_sessao_previa_indisponivel_para_anonimo(client):
    previa = baker.make(SessaoPlenaria, iniciada=False, publicar_pauta=False)

    response = client.get(reverse('sapl.sessao:resumo',
                                  kwargs={'pk': previa.pk}))

    assert response.status_code == 404


@pytest.mark.django_db(transaction=False)
def test_pauta_nao_publicada_indisponivel_para_anonimo(client):
    sem_pauta = baker.make(SessaoPlenaria, iniciada=True, publicar_pauta=False)

    response = client.get(reverse('sapl.sessao:pauta_sessao_detail',
                                  kwargs={'pk': sem_pauta.pk}))

    assert response.status_code == 404


def cria_sessao_com_parlamentares():
    legislatura = baker.make(Legislatura)
    sessao_legislativa = baker.make(SessaoLegislativa)
    tipo = baker.make(TipoSessaoPlenaria)
    sessao = baker.make(SessaoPlenaria,
                        legislatura=legislatura,
                        sessao_legislativa=sessao_legislativa,
                        tipo=tipo)
    parlamentares = [baker.make(Parlamentar, ativo=True) for _i in range(3)]
    return sessao, parlamentares


@pytest.mark.django_db(transaction=False)
def test_presenca_sessao_preserva_registros_ao_salvar_novamente(admin_client):
    # Cada salvamento apagava todas as presenças da sessão e as recriava,
    # trocando os ids. Além do desperdício, é essa janela entre apagar e
    # recriar que permite a duplicação quando o formulário é submetido duas
    # vezes em paralelo. Salvar de novo deve ser inócuo.
    sessao, parlamentares = cria_sessao_com_parlamentares()
    url = reverse('sapl.sessao:presenca', kwargs={'pk': sessao.pk})
    dados = {'presenca_ativos': [str(p.pk) for p in parlamentares]}

    admin_client.post(url, dados, follow=True)
    presencas = SessaoPlenariaPresenca.objects.filter(sessao_plenaria=sessao)
    ids_iniciais = sorted(presencas.values_list('id', flat=True))

    admin_client.post(url, dados, follow=True)
    admin_client.post(url, dados, follow=True)

    assert presencas.count() == len(parlamentares)
    assert sorted(presencas.values_list('parlamentar_id', flat=True)) == \
        sorted(p.pk for p in parlamentares)
    assert sorted(presencas.values_list('id', flat=True)) == ids_iniciais


@pytest.mark.django_db(transaction=False)
def test_presenca_sessao_ignora_registro_ja_existente(admin_client):
    # Reproduz o efeito da submissão concorrente: a linha já existe quando a
    # view vai gravar. Deve terminar com uma única presença, sem erro.
    sessao, parlamentares = cria_sessao_com_parlamentares()
    parlamentar = parlamentares[0]
    SessaoPlenariaPresenca.objects.create(sessao_plenaria=sessao,
                                          parlamentar=parlamentar)

    url = reverse('sapl.sessao:presenca', kwargs={'pk': sessao.pk})
    response = admin_client.post(
        url, {'presenca_ativos': [str(parlamentar.pk)]}, follow=True)

    assert response.status_code == 200
    assert SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao, parlamentar=parlamentar).count() == 1


@pytest.mark.django_db(transaction=False)
def test_presenca_sessao_remove_desmarcados(admin_client):
    sessao, parlamentares = cria_sessao_com_parlamentares()
    url = reverse('sapl.sessao:presenca', kwargs={'pk': sessao.pk})

    admin_client.post(url, {'presenca_ativos': [str(p.pk)
                                                for p in parlamentares]},
                      follow=True)
    admin_client.post(url, {'presenca_ativos': [str(parlamentares[0].pk)]},
                      follow=True)

    presencas = SessaoPlenariaPresenca.objects.filter(sessao_plenaria=sessao)
    assert list(presencas.values_list('parlamentar_id', flat=True)) == \
        [parlamentares[0].pk]


@pytest.mark.django_db(transaction=False)
def test_presenca_ordem_dia_preserva_registros_ao_resalvar(admin_client):
    sessao, parlamentares = cria_sessao_com_parlamentares()
    url = reverse('sapl.sessao:presencaordemdia', kwargs={'pk': sessao.pk})
    dados = {'presenca_ativos': [str(p.pk) for p in parlamentares]}

    admin_client.post(url, dados, follow=True)
    presencas = PresencaOrdemDia.objects.filter(sessao_plenaria=sessao)
    ids_iniciais = sorted(presencas.values_list('id', flat=True))

    admin_client.post(url, dados, follow=True)

    assert presencas.count() == len(parlamentares)
    assert sorted(presencas.values_list('id', flat=True)) == ids_iniciais


@pytest.mark.django_db(transaction=False)
def test_presenca_unica_por_sessao_e_parlamentar():
    # A restrição de unicidade é a proteção contra submissões concorrentes,
    # que a lógica da view sozinha não cobre.
    sessao, parlamentares = cria_sessao_com_parlamentares()
    parlamentar = parlamentares[0]

    for model in (SessaoPlenariaPresenca, PresencaOrdemDia):
        model.objects.create(sessao_plenaria=sessao, parlamentar=parlamentar)
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                model.objects.create(sessao_plenaria=sessao,
                                     parlamentar=parlamentar)
