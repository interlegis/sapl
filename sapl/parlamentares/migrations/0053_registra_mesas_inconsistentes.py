import logging

from django.db import migrations
from django.db.models import Q

logger = logging.getLogger(__name__)


def _data(d):
    return d.strftime('%d/%m/%Y')


def _descricao(mesa):
    return 'Mesa Diretora id={} ({}, {} a {})'.format(
        mesa.id, mesa.titulo or 'sem título',
        _data(mesa.data_inicio), _data(mesa.data_fim))


def mesas_inconsistentes(MesaDiretora):
    """
    Lista (mesa, motivo) para cada mesa que não passaria em
    MesaDiretora.clean(): datas invertidas, fora do período da legislatura
    ou sobrepostas a outra mesa da mesma legislatura (mesma regra de
    encosto do model).
    """
    problemas = []
    mesas = MesaDiretora.objects.select_related('legislatura').order_by(
        'legislatura__data_inicio', 'data_inicio', 'id')
    for mesa in mesas:
        leg = mesa.legislatura
        if mesa.data_inicio > mesa.data_fim:
            problemas.append((mesa, 'data de início posterior à data de fim'))
        if mesa.data_inicio < leg.data_inicio or mesa.data_fim > leg.data_fim:
            problemas.append((mesa, 'fora do período da legislatura {} '
                                    '({} a {})'.format(
                                        leg.numero, _data(leg.data_inicio),
                                        _data(leg.data_fim))))
        encosto = (
            Q(data_fim=mesa.data_inicio) | Q(data_inicio=mesa.data_fim)
        ) & ~Q(data_inicio=mesa.data_inicio, data_fim=mesa.data_fim)
        sobrepostas = list(MesaDiretora.objects.filter(
            legislatura_id=mesa.legislatura_id,
            data_inicio__lte=mesa.data_fim,
            data_fim__gte=mesa.data_inicio
        ).exclude(pk=mesa.pk).exclude(encosto).order_by('id').values_list(
            'id', flat=True))
        if sobrepostas:
            problemas.append((mesa, 'sobrepõe-se à(s) mesa(s) id={}'.format(
                ', '.join(str(i) for i in sobrepostas))))
    return problemas


def registrar_mesas_inconsistentes(apps, schema_editor):
    """
    A 0047 copiou para cada mesa as datas da sua sessão legislativa. Em
    bases antigas, essas datas podem cair fora do período da legislatura ou
    coincidir com as de outra mesa. A mesa continua visível, mas só pode
    ser editada depois de ajustar as datas.

    Esta migration não altera dados: registra essas mesas no log da
    aplicação e na saída do migrate, para ajuste manual pela Casa.
    """
    MesaDiretora = apps.get_model('parlamentares', 'MesaDiretora')
    problemas = mesas_inconsistentes(MesaDiretora)
    if not problemas:
        return

    linhas = ['{}: {}.'.format(_descricao(mesa), motivo)
              for mesa, motivo in problemas]
    resumo = ('{} problema(s) em mesas diretoras após a migração. Essas '
              'mesas só poderão ser editadas depois de ajustar as datas '
              'em Mesa Diretora.').format(len(problemas))

    print('\n  ' + resumo)
    for linha in linhas:
        print('    - ' + linha)
        logger.warning(linha)
    logger.warning(resumo)


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0052_auto_20261117_1700'),
    ]

    operations = [
        migrations.RunPython(registrar_mesas_inconsistentes,
                             reverse_code=migrations.RunPython.noop),
    ]
