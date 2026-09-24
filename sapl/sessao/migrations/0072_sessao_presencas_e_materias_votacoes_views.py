from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Views Postgres portadas de feat/painel-votacao-v2 (migration
    0070_views_sessao_plenaria.py naquela branch — o número colide com
    0070/0071 desta branch por coincidência de ponto de fork comum,
    daí o 0072 aqui), com correções para preservar exatamente o
    comportamento atual de sapl/painel/views.py:
      - COALESCE usa 'Sem Registro' (texto atual), não 'SEM PARTIDO'.
      - id da view é o da própria linha de presença, não o do parlamentar.
      - Sem checagem de intervalo de datas do Mandato (código atual não
        checa; a view original checava, o que é mais estrito e mudaria
        quem aparece como presente).
      - reverse_sql explícito (a migration original não tinha nenhum,
        deixando-a irreversível).
      - sessao_oradores_view não é portada (bug real no ON da LATERAL,
        e não é o alvo do N+1 que esta mudança resolve).
    """

    dependencies = [
        ('sessao', '0071_votacao_aberta_unique_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='votoparlamentar',
            name='votado_pelo_parlamentar',
            field=models.BooleanField(
                default=False,
                help_text='Marca se este voto foi lançado pelo próprio parlamentar '
                          '(voto individual/tablet) — distinto de um registro feito '
                          'pela Mesa/operador em nome dele.',
                verbose_name='Votado pelo parlamentar'),
        ),
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS sessao_presencas_view;
                CREATE VIEW sessao_presencas_view AS
                --
                -- PRESENCAS DE PARLAMENTARES COM FILIACAO (SE HOUVER)
                --   PARLAMENTAR DEVE ESTAR ATIVO E TER MANDATO NA LEGISLATURA
                --   DA SESSAO (sem checagem de intervalo de datas do
                --   mandato — igual ao comportamento Python atual)
                --
                -- EXPEDIENTE
                SELECT
                  presenca.id,
                  presenca.sessao_plenaria_id,
                  'expediente' AS etapa_sessao,
                  p.id as parlamentar_id,
                  p.nome_parlamentar as nome_parlamentar,
                  COALESCE(af.sigla, 'Sem Registro') AS filiacao,
                  p.ativo
                FROM sessao_sessaoplenariapresenca AS presenca
                JOIN sessao_sessaoplenaria AS sp
                  ON presenca.sessao_plenaria_id = sp.id
                JOIN parlamentares_parlamentar AS p
                  ON presenca.parlamentar_id = p.id
                JOIN parlamentares_mandato AS m
                  ON p.id = m.parlamentar_id
                  AND m.legislatura_id = sp.legislatura_id
                LEFT JOIN LATERAL (
                  SELECT pa.sigla
                  FROM parlamentares_filiacao f
                  JOIN parlamentares_partido pa ON pa.id = f.partido_id
                  WHERE f.parlamentar_id = p.id
                    AND f.data <= sp.data_inicio
                    AND (f.data_desfiliacao IS NULL OR f.data_desfiliacao >= sp.data_inicio)
                  ORDER BY f.data DESC
                  LIMIT 1
                ) AS af ON TRUE
                WHERE p.ativo = TRUE

                UNION ALL

                -- ORDEM DO DIA
                SELECT
                  presenca.id,
                  presenca.sessao_plenaria_id,
                  'ordemdia' AS etapa_sessao,
                  p.id as parlamentar_id,
                  p.nome_parlamentar as nome_parlamentar,
                  COALESCE(af.sigla, 'Sem Registro') AS filiacao,
                  p.ativo
                FROM sessao_presencaordemdia AS presenca
                JOIN sessao_sessaoplenaria AS sp
                  ON presenca.sessao_plenaria_id = sp.id
                JOIN parlamentares_parlamentar AS p
                  ON presenca.parlamentar_id = p.id
                JOIN parlamentares_mandato AS m
                  ON p.id = m.parlamentar_id
                  AND m.legislatura_id = sp.legislatura_id
                LEFT JOIN LATERAL (
                  SELECT pa.sigla
                  FROM parlamentares_filiacao f
                  JOIN parlamentares_partido pa ON pa.id = f.partido_id
                  WHERE f.parlamentar_id = p.id
                    AND f.data <= sp.data_inicio
                    AND (f.data_desfiliacao IS NULL OR f.data_desfiliacao >= sp.data_inicio)
                  ORDER BY f.data DESC
                  LIMIT 1
                ) AS af ON TRUE
                WHERE p.ativo = TRUE
                ORDER BY sessao_plenaria_id, etapa_sessao, nome_parlamentar
            """,
            reverse_sql="DROP VIEW IF EXISTS sessao_presencas_view;",
        ),
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS sessao_materias_votacoes_view;
                CREATE VIEW sessao_materias_votacoes_view AS
                --
                -- Votacao de Materias (Simbolica/Nominal/Secreta) — Leitura
                -- (tipo_votacao=4) fica de fora, ela não usa este caminho.
                --
                -- EXPEDIENTE
                WITH votacao_materias AS (
                SELECT  em.sessao_plenaria_id,
                        em.id id,
                        'expediente' etapa_sessao,
                        em.numero_ordem,
                        em.materia_id,
                        tm.descricao||' nº '||ml.numero||' de '||ml.ano as materia_texto,
                        ml.ementa materia_ementa,
                        tipo_votacao,
                        CASE tipo_votacao
                            WHEN 1 THEN 'Simbólica'
                            WHEN 2 THEN 'Nominal'
                            WHEN 3 THEN 'Secreta'
                            WHEN 4 THEN 'Leitura'
                            ELSE ''
                        END as tipo_votacao_descricao,
                        resultado_votacao,
                        em.resultado,
                        numero_votos,
                        votos_parlamentares,
                        votacao_aberta
                FROM sessao_expedientemateria em
                JOIN materia_materialegislativa ml ON (em.materia_id = ml.id)
                JOIN materia_tipomaterialegislativa tm ON (ml.tipo_id = tm.id)
                LEFT JOIN LATERAL (
                    SELECT jsonb_build_object(
                                'votos_sim', coalesce(rv.numero_votos_sim, 0),
                                'votos_nao', coalesce(rv.numero_votos_nao, 0),
                                'abstencoes', coalesce(rv.numero_abstencoes, 0),
                                'total_votos', coalesce(rv.numero_votos_sim, 0) +
                                    coalesce(rv.numero_votos_nao, 0) +
                                    coalesce(rv.numero_abstencoes, 0)
                            ) as numero_votos,
                            trv.nome resultado_votacao
                    FROM sessao_registrovotacao rv
                    JOIN sessao_tiporesultadovotacao trv on (rv.tipo_resultado_votacao_id = trv.id)
                    WHERE rv.expediente_id = em.id AND tipo_votacao != 4) rv ON TRUE
                LEFT JOIN LATERAL (
                    SELECT em.sessao_plenaria_id,
                           em.numero_ordem,
                           jsonb_object_agg(
                                    vp.parlamentar_id,
                                    jsonb_build_object(
                                      'materia_id', em.materia_id,
                                      'parlamentar_id', vp.parlamentar_id,
                                      'parlamentar_nome', p.nome_parlamentar,
                                      'voto', vp.voto,
                                      'votado_pelo_parlamentar', vp.votado_pelo_parlamentar
                                     )) as votos_parlamentares
                    FROM sessao_votoparlamentar vp
                    JOIN parlamentares_parlamentar p ON (vp.parlamentar_id = p.id)
                    WHERE vp.expediente_id = em.id AND em.tipo_votacao != 4
                    GROUP BY em.sessao_plenaria_id, em.numero_ordem
                ) vp ON TRUE

                UNION ALL

                -- ORDEM DIA
                SELECT  od.sessao_plenaria_id,
                        od.id id,
                        'ordemdia' etapa_sessao,
                        od.numero_ordem,
                        od.materia_id,
                        tm.descricao||' nº '||ml.numero||' de '||ml.ano as materia_texto,
                        ml.ementa,
                        tipo_votacao,
                        CASE tipo_votacao
                            WHEN 1 THEN 'Simbólica'
                            WHEN 2 THEN 'Nominal'
                            WHEN 3 THEN 'Secreta'
                            WHEN 4 THEN 'Leitura'
                            ELSE ''
                        END as tipo_votacao_descricao,
                        resultado_votacao,
                        od.resultado,
                        numero_votos,
                        votos_parlamentares,
                        votacao_aberta
                FROM sessao_ordemdia od
                JOIN materia_materialegislativa ml ON (od.materia_id = ml.id)
                JOIN materia_tipomaterialegislativa tm ON (ml.tipo_id = tm.id)
                LEFT JOIN LATERAL (
                    SELECT jsonb_build_object(
                                'votos_sim', coalesce(rv.numero_votos_sim, 0),
                                'votos_nao', coalesce(rv.numero_votos_nao, 0),
                                'abstencoes', coalesce(rv.numero_abstencoes, 0),
                                'total_votos', coalesce(rv.numero_votos_sim, 0) +
                                    coalesce(rv.numero_votos_nao, 0) +
                                    coalesce(rv.numero_abstencoes, 0)
                            ) as numero_votos,
                            trv.nome resultado_votacao
                    FROM sessao_registrovotacao rv
                    JOIN sessao_tiporesultadovotacao trv on (rv.tipo_resultado_votacao_id = trv.id)
                    WHERE rv.ordem_id = od.id AND tipo_votacao != 4) rv ON TRUE
                LEFT JOIN LATERAL (
                    SELECT od.sessao_plenaria_id,
                           od.numero_ordem,
                           jsonb_object_agg(
                                    vp.parlamentar_id,
                                    jsonb_build_object(
                                      'materia_id', od.materia_id,
                                      'parlamentar_id', vp.parlamentar_id,
                                      'parlamentar_nome', p.nome_parlamentar,
                                      'voto', vp.voto,
                                      'votado_pelo_parlamentar', vp.votado_pelo_parlamentar
                                     )) as votos_parlamentares
                    FROM sessao_votoparlamentar vp
                    JOIN parlamentares_parlamentar p ON (vp.parlamentar_id = p.id)
                    WHERE vp.ordem_id = od.id AND od.tipo_votacao != 4
                    GROUP BY od.sessao_plenaria_id, od.numero_ordem
                ) vp ON TRUE
                )
                SELECT *
                FROM votacao_materias
                ORDER BY sessao_plenaria_id, etapa_sessao, numero_ordem
            """,
            reverse_sql="DROP VIEW IF EXISTS sessao_materias_votacoes_view;",
        ),
    ]
