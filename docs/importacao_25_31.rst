Instruções para Importação da base mysql 2.5
============================================

Instalar Dependências::

   pip install -r requirements/migration-requirements.txt

Criar um arquivo sapl/legacy/.env com o seguinte conteúdo (parametros de acesso ao banco 2.5)::

   DATABASE_URL = mysql://[usuario do mysql]:[senha do myuysql]@[host]:[porta]/[banco]


o conteúdo do arquivo será semelhante a isso::

   DATABASE_URL = mysql://sapl:sapl@localhost:3306/interlegis

Para entrar no ambiente virtual::

   workon sapl

Posteriormente rodar a seguinte sequencia de comandos estando no ambiente virtual::

   ./manage.py shell --settings=sapl.legacy_migration_settings
   
   %run sapl/legacy/migration.py
   
   migrate()
