import logging

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import DEFAULT_DB_ALIAS

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check ids sequences and update them'

    def handle(self, *args, **kwargs):
        models = apps.get_models()

        for model in models:
            if model._meta.managed and model._meta.auto_field:
                fn_check_sequence_for_model(model)


def fn_check_sequence_for_model(model):
    SP_NAME = fn_check_sequence_for_model.__name__

    with connection.cursor() as c:
        try:
            c.callproc(SP_NAME, [model._meta.db_table])
        except Exception as e:
            if f"function {SP_NAME}(unknown) does not exist" not in str(e):
                # Se ocorreu um erro e não é por inexistência da SP
                logger.error(f"Falha na execução da Store Procedure para a tabela {model._meta.db_table}. {str(e)}")
            else:
                # se a execução da SP falhou por ela não existir
                try:
                    # cria a SP
                    c.execute(
                        f"""
                        CREATE OR REPLACE FUNCTION {SP_NAME}(IN table_name character varying) RETURNS integer AS
                            $$
                            DECLARE
                                max_id integer := 0;
                            BEGIN
                                EXECUTE format('SELECT setval(pg_get_serial_sequence(''%s'',''id''), coalesce(max(id), 1), max(id) IS NOT null) FROM %s', table_name, table_name ) INTO max_id;
                                if max_id is null then
                                    EXECUTE format('DROP SEQUENCE IF EXISTS %s_id_seq cascade', table_name);
                                    EXECUTE format('CREATE SEQUENCE %s_id_seq start 1 OWNED BY %s.id', table_name, table_name);
                                    EXECUTE format('ALTER TABLE %s ALTER COLUMN id SET DEFAULT nextval(''%s_id_seq''::regclass)', table_name, table_name);
                                    EXECUTE format('SELECT setval(pg_get_serial_sequence(''%s'',''id''), coalesce(max(id), 1), max(id) IS NOT null) FROM %s', table_name, table_name ) INTO max_id;
                                end if;
                                return max_id;
                            END;
                            $$ LANGUAGE plpgsql;
                        """
                    )
                except Exception as e:
                    # se falhou na criação
                    logger.error(f"Falha na criação da Store Procedure {SP_NAME} para o tabela {model._meta.db_table}. {str(e)}")
                    logger.error(f"Falha na criação da Store Procedure {SP_NAME} para o tabela {model._meta.db_table}. {str(e)}")
                try:
                    # tenta executá-la após criação.
                    c.callproc(SP_NAME, [model._meta.db_table])
                except Exception as e:
                    # se falhou na execução
                    logger.error(f"Falha na execução da Store Procedure {SP_NAME} para o tabela {model._meta.db_table}. {str(e)}")

        finally:
            c.close()
