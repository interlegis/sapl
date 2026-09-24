from django.db import migrations, models

_OLD_VIEW = """
    create or replace view materia_materiaemtramitacao as
    select m.id as id,
           m.id as materia_id,
           t.id as tramitacao_id,
           t.unidade_tramitacao_destino_id as unidade_tramitacao_atual_id
    from materia_materialegislativa m
    inner join materia_tramitacao t on (m.id = t.materia_id)
    where t.id = (select max(id) from materia_tramitacao where materia_id = m.id)
    order by m.id DESC
"""

_NEW_VIEW = """
    CREATE OR REPLACE VIEW materia_materiaemtramitacao AS
    SELECT
        m.id,
        m.id AS materia_id,
        t.id AS tramitacao_id,
        t.unidade_tramitacao_destino_id AS unidade_tramitacao_atual_id
    FROM materia_materialegislativa m
    JOIN LATERAL (
        SELECT
            t.id,
            t.unidade_tramitacao_destino_id
        FROM materia_tramitacao t
        WHERE t.materia_id = m.id
        ORDER BY t.id DESC
        LIMIT 1
    ) t ON true;
"""


class Migration(migrations.Migration):
    # CREATE INDEX CONCURRENTLY cannot run inside a transaction.
    atomic = False

    dependencies = [
        ('materia', '0087_update_viewdb_materiaemtramitacao'),
    ]

    operations = [
        migrations.RunSQL(sql=_NEW_VIEW, reverse_sql=_OLD_VIEW),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS
                            tram_materia_id_desc
                        ON materia_tramitacao (materia_id, id DESC)
                    """,
                    reverse_sql="""
                        DROP INDEX CONCURRENTLY IF EXISTS
                            tram_materia_id_desc
                    """,
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name='tramitacao',
                    index=models.Index(
                        fields=['materia', '-id'],
                        name='tram_materia_id_desc',
                    ),
                ),
            ],
        ),
    ]
