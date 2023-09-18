from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0041_auto_20220814_2235'),
    ]

    operations = [
        migrations.RunSQL("""
drop view if exists norma_viewnormasestatisticas;
create or replace view norma_viewnormasestatisticas as
select row_number() OVER() as id, * from (
    SELECT
         ROW_NUMBER() OVER (
                PARTITION BY ano_est, mes_est
                ORDER BY ano_est, mes_est desc, norma_count desc
            )::smallint AS "mais_acessadas"
        ,
        *
    from (
         SELECT
             "norma_normaestatisticas"."norma_id" as norma_id,
             extract(year from horario_acesso) as ano_est,
             extract(month from horario_acesso) as mes_est,
             count(*) as norma_count,
             "norma_normajuridica"."numero" as norma_numero,
             "norma_normajuridica"."ano" as norma_ano,
             "norma_normajuridica"."data" as norma_data,
             "norma_tiponormajuridica"."sigla" as norma_tipo_sigla,
             "norma_tiponormajuridica"."descricao" as norma_tipo_descricao,
             "norma_normajuridica"."ementa" as norma_ementa,
             "norma_normajuridica"."observacao" as norma_observacao
         from norma_normaestatisticas
            INNER JOIN "norma_normajuridica" ON ("norma_normaestatisticas"."norma_id" = "norma_normajuridica"."id")
            INNER JOIN "norma_tiponormajuridica" ON ("norma_normajuridica"."tipo_id" = "norma_tiponormajuridica"."id")
         group by
             "norma_normaestatisticas"."norma_id",
             ano_est,
             mes_est,
             norma_numero,
             norma_ano,
             norma_data,
             norma_ementa,
             norma_observacao,
             norma_tipo_sigla,
             norma_tipo_descricao
         order by ano_est, mes_est desc, norma_count desc, norma_ano desc
    ) as subquery
) as query_final
    order by ano_est, mes_est desc, mais_acessadas;
        """),
    ]