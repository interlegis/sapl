from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('sessao', '0053_auto_20200609_1501'),
    ]

    operations = [
        migrations.RunSQL(
            """
                create or replace view sessao_expedientepauta as
                with autoria_materia as (
                    select ma.materia_id, array_agg(ba.nome) as autores
                    from materia_autoria ma
                    join base_autor ba on (ma.autor_id = ba.id)
                    group by ma.materia_id
                    order by ma.materia_id, autores
                ),
                tramitacao_numeracao_materia as (
                    select distinct on (m.id)
                        m.id as materia_id,
                        mt.id as tramitacao_id,
                        mn.id as numeracao_id
                    from materia_materialegislativa as m
                    left join materia_tramitacao mt on (m.id = mt.materia_id)
                    left join materia_numeracao mn on (m.id = mn.materia_id)
                    order by materia_id, mt.data_tramitacao DESC, mt.id DESC,
                             mn.id DESC
                ),
                sessao_expedientepauta as (
                    select ex.id as id,
                           ex.id as expediente_id,
                           ex.sessao_plenaria_id as sessao_plenaria_id,
                           tnm.materia_id as materia_id,
                           tnm.tramitacao_id as tramitacao_id,
                           tnm.numeracao_id as numeracao_id,
                           am.autores as autores
                    from sessao_expedientemateria ex
                    join tramitacao_numeracao_materia tnm on (
                        ex.materia_id = tnm.materia_id
                    )
                    left join autoria_materia am on (
                        ex.materia_id = am.materia_id
                    )
                )
                select *
                from sessao_expedientepauta
            """
        )
    ]
