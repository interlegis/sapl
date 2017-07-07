Instruções para Importação da base mysql 2.5
============================================


Para entrar no ambiente virtual::

   workon sapl



Instalar Dependências::

   pip3 install -r requirements/migration-requirements.txt

Criar um arquivo sapl/legacy/.env com o seguinte conteúdo (parametros de acesso ao banco 2.5)::

   DATABASE_URL = mysql://[usuario do mysql]:[senha do myuysql]@[host]:[porta]/[banco]


o conteúdo do arquivo será semelhante a isso::

   DATABASE_URL = mysql://sapl:sapl@localhost:3306/interlegis


Posteriormente rodar a seguinte sequencia de comandos estando no ambiente virtual::

   ./manage.py shell --settings=sapl.legacy_migration_settings

   %run sapl/legacy/migration.py

   migrate()


Migração de documentos do sapl 2.5
----------------------------------

No sapl 2.5 todos os documentos ficavam armazenados no ZODB (o banco do Zope).
No sapl 3.1 eles ficam no sistema de arquivos convencional e portanto precisam:

1. ser exportados para o sistema de arquivos
2. ser vinculados ao novo banco importado para o sapl 3.1


Exportar os documentos para o sistema de arquivos
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Siga os seguintes passos:

1. Instale o `Products.FSDump` no sapl 2.5.

   Para isso basta colocar a pasta `Products/FSDump` do projeto https://github.com/zopefoundation/Products.FSDump na pasta `Products` da instalação do sapl 2.5 e reiniciar o Zope.

   A pasta a ser instalada é a seguinte:
   https://github.com/zopefoundation/Products.FSDump/tree/master/Products/FSDump

2. Na ZMI, na pasta `sapl_documentos`, adicione um objeto do tipo `Dumper`:

   - Em `Filesystem path` escolha uma pasta do sistema de arquivos local para onde os arquivos serão copiados
   - Desmarque a opção `Use .metadata file`
   - Clique no botão `Add`

3. Use o objeto `Dumper` criado para exportar os arquivos:

   - Clique no objeto `Dumper` criado para ver suas opções
   - Confira seus parametros e clique em `Change and Dump`
   - Aguarde a exportação dos arquivos e verifique que foram copiados para a pasta indicada


Vincular os documentos ao novo banco do sapl 3.1
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Primeiramente migre o banco do sapl 2.5 para o sapl 3.1

2. Copie a pasta exportada `sapl_documentos` dentro da pasta `media` da instalação do sapl 3.1

3. De forma semelhante ao realizado na migração do banco, dentro no mesmo ambiente virtual, rode os seguintes comandos::

    ./manage.py shell --settings=sapl.legacy_migration_settings

    %run sapl/legacy/migracao_documentos.py

    migrar_documentos()
    
    
Para indexar os arquivos para pesquisa textual
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. workon sapl
2. ./manage.py rebuild_index


Dependendo da quantidade de arquivos a serem indexados, pode ser listado o seguinte erro 'Too many open files'

Isto está ligado a quantidade máxima de aquivos que podem ser abertos ao mesmo tempo pelo sistema operacional

Para aumentar este limite::

   sudo nano /etc/security/limits.conf
   *       soft    nofile  9000
   *       hard    nofile  65000


   sudo nano /etc/pam.d/common-session
   session required pam_limits.so

Após reiniciar, verificar se foram carregados os novos parâmetros com o comando::
   ulimit -a

deve ser apresentado o seguinte::
   open files                      (-n) 9000


