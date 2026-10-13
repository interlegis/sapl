"""
Gravação em lote dos dados de uma Sessão Plenária.

Recebe, numa única requisição, presenças da sessão, presenças da ordem do
dia, votações (registro + votos nominais) e atualizações de matérias da
ordem do dia/expediente. Ver docs/api-sessao-lote.md.

Regras:
    - qualquer combinação de blocos é aceita; o que não for enviado não é
      alterado;
    - cada item é gravado em sua própria transação: a falha de um não
      impede a gravação dos demais;
    - cada item devolve um status (criado, atualizado, removido, inalterado
      ou erro) para que o cliente reenvie apenas o que falhou;
    - reenviar o mesmo lote não duplica presenças nem votos;
    - validações vêm dos mesmos serializers e as permissões são as mesmas
      exigidas pelos endpoints individuais de cada model.
"""
import logging

from django.db import transaction
from rest_framework import serializers

from drfautoapi.drfautoapi import ApiViewSetConstrutor
from sapl.parlamentares.models import Parlamentar
from sapl.sessao.models import (ExpedienteMateria, OrdemDia,
                                PresencaOrdemDia, RegistroVotacao,
                                SessaoPlenariaPresenca, VotoParlamentar)
from sapl.utils import get_client_ip


logger = logging.getLogger(__name__)

MAX_ITENS_POR_BLOCO = 500

CRIADO = 'criado'
ATUALIZADO = 'atualizado'
REMOVIDO = 'removido'
INALTERADO = 'inalterado'
ERRO = 'erro'

VOTO_SIM = 'Sim'
VOTO_NAO = 'Não'
VOTO_ABSTENCAO = 'Abstenção'
VOTO_NAO_VOTOU = 'Não Votou'
VOTOS_VALIDOS = (VOTO_SIM, VOTO_NAO, VOTO_ABSTENCAO, VOTO_NAO_VOTOU)

BLOCOS = (
    'presencas_sessao',
    'presencas_ordem_dia',
    'votacoes',
    'ordens_dia',
    'expedientes_materia',
)


class ItemInvalido(Exception):

    def __init__(self, erros):
        super().__init__(erros)
        self.erros = erros


def perm(model, acao):
    return '{}.{}_{}'.format(
        model._meta.app_label, acao, model._meta.model_name)


def serializer_class_for(model):
    return ApiViewSetConstrutor.get_viewset_for_model(model).serializer_class


class SessaoLote:

    def __init__(self, sessao, request):
        self.sessao = sessao
        self.request = request
        self.user = request.user
        self.ip = get_client_ip(request)

    @classmethod
    def validar_payload(cls, data):
        """Valida apenas a estrutura do lote. Erros aqui recusam o lote
        inteiro (HTTP 400); erros de item são reportados por item."""
        if not isinstance(data, dict):
            raise serializers.ValidationError(
                'O corpo da requisição deve ser um objeto JSON.')

        desconhecidos = sorted(set(data) - set(BLOCOS))
        if desconhecidos:
            raise serializers.ValidationError({
                k: 'Bloco desconhecido. Blocos aceitos: {}.'.format(
                    ', '.join(BLOCOS)) for k in desconhecidos})

        if not any(b in data for b in BLOCOS):
            raise serializers.ValidationError(
                'Informe ao menos um dos blocos: {}.'.format(
                    ', '.join(BLOCOS)))

        erros = {}
        for bloco in BLOCOS:
            if bloco not in data:
                continue
            itens = data[bloco]
            if not isinstance(itens, list):
                erros[bloco] = 'Deve ser uma lista.'
            elif len(itens) > MAX_ITENS_POR_BLOCO:
                erros[bloco] = 'Máximo de {} itens por bloco.'.format(
                    MAX_ITENS_POR_BLOCO)
            elif not all(isinstance(i, dict) for i in itens):
                erros[bloco] = 'Todos os itens devem ser objetos JSON.'
        if erros:
            raise serializers.ValidationError(erros)

    def processar(self, data):
        self.validar_payload(data)

        # Presenças antes das votações e votações antes das atualizações de
        # matéria, na mesma ordem em que as integrações fariam com os
        # endpoints individuais.
        relatorio = {'sessao_plenaria': self.sessao.pk}
        processadores = (
            ('presencas_sessao', lambda i: self.presenca(
                SessaoPlenariaPresenca, i)),
            ('presencas_ordem_dia', lambda i: self.presenca(
                PresencaOrdemDia, i)),
            ('votacoes', self.votacao),
            ('ordens_dia', lambda i: self.materia(OrdemDia, i)),
            ('expedientes_materia', lambda i: self.materia(
                ExpedienteMateria, i)),
        )
        for bloco, processador in processadores:
            if bloco in data:
                relatorio[bloco] = [
                    self.processar_item(processador, item)
                    for item in data[bloco]]

        resumo = dict.fromkeys(
            (CRIADO, ATUALIZADO, REMOVIDO, INALTERADO, ERRO), 0)
        for bloco in BLOCOS:
            for item in relatorio.get(bloco, []):
                resumo[item['status']] += 1
        relatorio['resumo'] = resumo

        logger.info('user={}. Lote da sessão plenária (pk={}) processado: '
                    '{}'.format(self.user.username, self.sessao.pk, resumo))
        return relatorio

    def processar_item(self, processador, item):
        try:
            with transaction.atomic():
                return processador(item)
        except ItemInvalido as e:
            return self.item_erro(item, e.erros)
        except serializers.ValidationError as e:
            return self.item_erro(item, e.detail)
        except Exception as e:
            logger.error('user={}. Erro ao processar item do lote da sessão '
                         'plenária (pk={}): {}. {}'.format(
                             self.user.username, self.sessao.pk, item, e))
            return self.item_erro(item, str(e))

    def item_erro(self, item, erros):
        chaves = ('parlamentar', 'ordem', 'expediente', 'id')
        r = {k: item[k] for k in chaves if k in item}
        r.update(status=ERRO, erros=erros)
        return r

    def exigir_perms(self, *perms):
        faltando = [p for p in perms if not self.user.has_perm(p)]
        if faltando:
            raise ItemInvalido(
                'Usuário sem permissão: {}.'.format(', '.join(faltando)))

    def parlamentar_id(self, valor, campo='parlamentar'):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ItemInvalido({campo: 'Informe o id do parlamentar.'})
        if not Parlamentar.objects.filter(pk=valor).exists():
            raise ItemInvalido(
                {campo: 'Parlamentar (pk={}) não existe.'.format(valor)})
        return valor

    def presenca(self, model, item):
        """{"parlamentar": <id>, "presente": true|false}"""
        parlamentar = self.parlamentar_id(item.get('parlamentar'))
        presente = item.get('presente', True)
        if not isinstance(presente, bool):
            raise ItemInvalido({'presente': 'Deve ser true ou false.'})

        r = {'parlamentar': parlamentar, 'presente': presente}
        existentes = model.objects.filter(
            sessao_plenaria=self.sessao, parlamentar_id=parlamentar)

        if not presente:
            if not existentes.exists():
                return dict(r, status=INALTERADO)
            self.exigir_perms(perm(model, 'delete'))
            existentes.delete()
            return dict(r, status=REMOVIDO)

        atual = existentes.first()
        if atual:
            return dict(r, status=INALTERADO, id=atual.pk)

        self.exigir_perms(perm(model, 'add'))
        dados = {'sessao_plenaria': self.sessao.pk,
                 'parlamentar': parlamentar}
        if model is SessaoPlenariaPresenca:
            dados['data_sessao'] = self.sessao.data_inicio
        serializer = serializer_class_for(model)(
            data=dados, context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        return dict(r, status=CRIADO, id=obj.pk)

    def alvo_votacao(self, item):
        """Votação é de uma matéria da ordem do dia ou do expediente,
        nunca das duas (mesma regra de RegistroVotacao.clean)."""
        tem_ordem = item.get('ordem') is not None
        tem_expediente = item.get('expediente') is not None
        if tem_ordem == tem_expediente:
            raise ItemInvalido('Informe exatamente um dos campos '
                               '"ordem" ou "expediente".')
        campo, model = (('ordem', OrdemDia) if tem_ordem
                        else ('expediente', ExpedienteMateria))
        alvo = model.objects.filter(
            pk=item[campo], sessao_plenaria=self.sessao).first()
        if not alvo:
            raise ItemInvalido({campo: '{} (pk={}) não existe nesta sessão '
                                'plenária.'.format(
                                    model._meta.verbose_name, item[campo])})
        return campo, alvo

    def votos_do_item(self, item):
        votos = item['votos']
        if not isinstance(votos, list):
            raise ItemInvalido({'votos': 'Deve ser uma lista.'})

        erros = {}
        resultado = {}
        for i, v in enumerate(votos):
            if not isinstance(v, dict):
                erros[i] = 'Deve ser um objeto JSON.'
                continue
            try:
                p = self.parlamentar_id(v.get('parlamentar'))
            except ItemInvalido as e:
                erros[i] = e.erros
                continue
            if p in resultado:
                erros[i] = {'parlamentar': 'Parlamentar repetido.'}
            elif v.get('voto') not in VOTOS_VALIDOS:
                erros[i] = {'voto': 'Valores aceitos: {}.'.format(
                    ', '.join(VOTOS_VALIDOS))}
            else:
                resultado[p] = v['voto']
        if erros:
            raise ItemInvalido({'votos': erros})
        return resultado

    def votacao(self, item):
        """
        {"ordem"|"expediente": <id>, "tipo_resultado_votacao": <id>,
         "observacao": "...",
         "votos": [{"parlamentar": <id>, "voto": "Sim"}, ...]}

        Com "votos" (votação nominal), os totais são calculados a partir
        deles e a lista substitui os votos já gravados para a matéria. Sem
        "votos" (simbólica/secreta), informe numero_votos_sim,
        numero_votos_nao e numero_abstencoes.
        """
        campo, alvo = self.alvo_votacao(item)
        r = {campo: alvo.pk}

        votos = self.votos_do_item(item) if 'votos' in item else None

        dados = {
            campo: alvo.pk,
            'materia': alvo.materia_id,
            'tipo_resultado_votacao': item.get('tipo_resultado_votacao'),
            'observacao': item.get('observacao', ''),
        }
        totais = ('numero_votos_sim', 'numero_votos_nao', 'numero_abstencoes')
        if votos is not None:
            contagem = list(votos.values())
            calculados = dict(zip(totais, (
                contagem.count(VOTO_SIM),
                contagem.count(VOTO_NAO),
                contagem.count(VOTO_ABSTENCAO))))
            divergentes = {k: 'Diverge do total calculado a partir dos '
                           'votos ({}).'.format(calculados[k])
                           for k in totais
                           if k in item and item[k] != calculados[k]}
            if divergentes:
                raise ItemInvalido(divergentes)
            dados.update(calculados)
        else:
            dados.update({k: item.get(k) for k in totais})

        registro = RegistroVotacao.objects.filter(**{campo: alvo}).first()
        if registro:
            self.exigir_perms(perm(RegistroVotacao, 'change'))
        else:
            self.exigir_perms(perm(RegistroVotacao, 'add'))
        if votos is not None:
            self.exigir_perms(*(perm(VotoParlamentar, a)
                                for a in ('add', 'change', 'delete')))

        serializer = serializer_class_for(RegistroVotacao)(
            registro, data=dados, context={'request': self.request})
        serializer.is_valid(raise_exception=True)

        criado = registro is None
        alterado = criado or any(
            getattr(registro, f) != v
            for f, v in serializer.validated_data.items())
        if alterado:
            registro = serializer.save(user=self.user, ip=self.ip)

        if votos is not None and self.gravar_votos(campo, alvo, registro,
                                                   votos):
            alterado = True

        if criado:
            status = CRIADO
        else:
            status = ATUALIZADO if alterado else INALTERADO
        return dict(r, status=status, id=registro.pk)

    def gravar_votos(self, campo, alvo, registro, votos):
        """Upsert por (matéria, parlamentar). Remove votos de parlamentares
        fora da lista e votos sem registro, como a votação nominal da tela
        faz ao finalizar."""
        alterado = False
        existentes = {}
        for v in VotoParlamentar.objects.filter(**{campo: alvo}):
            if v.parlamentar_id in existentes or \
                    v.parlamentar_id not in votos:
                v.delete()
                alterado = True
            else:
                existentes[v.parlamentar_id] = v

        for parlamentar, voto in votos.items():
            v = existentes.get(parlamentar)
            if v and v.voto == voto and v.votacao_id == registro.pk:
                continue
            if not v:
                v = VotoParlamentar(parlamentar_id=parlamentar,
                                    **{campo: alvo})
            v.voto = voto
            v.votacao = registro
            v.user = self.user
            v.ip = self.ip
            v.save()
            alterado = True
        return alterado

    def materia(self, model, item):
        """{"id": <id>, <campos do PATCH do model>}"""
        pk = item.get('id')
        obj = model.objects.filter(
            pk=pk, sessao_plenaria=self.sessao).first() \
            if isinstance(pk, int) and not isinstance(pk, bool) else None
        if not obj:
            raise ItemInvalido({'id': '{} (pk={}) não existe nesta sessão '
                                'plenária.'.format(
                                    model._meta.verbose_name, pk)})

        dados = {k: v for k, v in item.items() if k != 'id'}
        if 'sessao_plenaria' in dados and \
                dados['sessao_plenaria'] != self.sessao.pk:
            raise ItemInvalido({'sessao_plenaria': 'Não é possível mover a '
                                'matéria para outra sessão pelo lote.'})
        self.exigir_perms(perm(model, 'change'))

        serializer = serializer_class_for(model)(
            obj, data=dados, partial=True, context={'request': self.request})
        serializer.is_valid(raise_exception=True)

        r = {'id': obj.pk}
        if not any(getattr(obj, f) != v
                   for f, v in serializer.validated_data.items()):
            return dict(r, status=INALTERADO)
        serializer.save()
        return dict(r, status=ATUALIZADO)
