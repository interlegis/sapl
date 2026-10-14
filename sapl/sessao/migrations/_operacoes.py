from django.db import migrations


class AddConstraintSeAusente(migrations.AddConstraint):
    """
    AddConstraint que aproveita um índice já existente com o mesmo nome, desde
    que ele seja único, válido e sobre as mesmas colunas. Se não for, falha em
    vez de registrar no estado do Django uma constraint que o banco não aplica.

    Antes de serem renumeradas no #3855, as migrations 0071 e 0072 se chamavam
    0070_votoparlamentar_unique_constraint e
    0071_votacao_aberta_unique_constraint e chegaram a ser aplicadas em alguns
    bancos de produção. Eles já têm os índices, mas não registram as migrations
    com os nomes atuais, e o AddConstraint puro falharia com DuplicateTable.
    """

    def database_forwards(self, app_label, schema_editor, from_state,
                          to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        nome = self.constraint.name
        connection = schema_editor.connection
        with connection.cursor() as cursor:
            existente = connection.introspection.get_constraints(
                cursor, model._meta.db_table).get(nome)
            if existente is not None:
                cursor.execute(
                    'SELECT indisvalid FROM pg_index '
                    'WHERE indexrelid = %s::regclass', [nome])
                existente['valid'] = cursor.fetchone()[0]

        if existente is None:
            super().database_forwards(
                app_label, schema_editor, from_state, to_state)
            return

        colunas = [model._meta.get_field(campo).column
                   for campo in self.constraint.fields]
        if not (existente['unique'] and existente['valid'] and
                existente['columns'] == colunas):
            raise ValueError(
                'O índice "{}" já existe, mas não é o índice único e válido '
                'sobre ({}) esperado pela constraint. Remova-o e rode o '
                'migrate de novo.'.format(nome, ', '.join(colunas)))
