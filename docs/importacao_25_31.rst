Instruções para Importação da base mysql 2.5
============================================


Criar um arquivo sapl/legacy/.env com o seguinte conteúdo (parametros de acesso ao banco 2.5)::

      DATABASE_URL = mysql://[usuario do mysql]:[senha do myuysql]@[host]:[porta]/[banco]


o conteúdo do arquivo será semelhante a isso:
DATABASE_URL = mysql://sapl:sapl@localhost:3306/interlegis


Posteriormente rodar a seguinte sequencia de comandos::


   ./manage.py shell_plus --settings=sapl.legacy_migration_settings
   
   >>> %run sapl/legacy/migration.py
   
   >>> migrate()
   
