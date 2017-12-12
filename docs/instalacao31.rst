Instalação do Ambiente de Desenvolvimento
=========================================

* Procedimento testado nos seguintes SO's:

  * `Ubuntu 16.04 64bits <https://github.com/interlegis/sapl/blob/master/README.rst>`_;

* Para esta instalação foi utilizado o usuário de sistema sapl31


Atualizar o sistema::
----------------------

 ::

    sudo apt-get update

    sudo apt-get upgrade



Instalar as seguintes dependências do sistema::
----------------------------------------------------------------------------------------

* ::

    sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config postgresql postgresql-contrib pgadmin3 python-psycopg2 \
    software-properties-common build-essential libxml2-dev libjpeg-dev \
    libmysqlclient-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools \
    python3-pip curl poppler-utils default-jre

    sudo -i
    curl -sL https://deb.nodesource.com/setup_5.x | bash -
    exit
    sudo apt-get install nodejs

    sudo npm install npm -g
    sudo npm install -g bower

Instalar o virtualenv usando python 3 para o projeto.
-----------------------------------------------------

* Para usar `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_, instale com::

    sudo pip3 install virtualenvwrapper

    sudo mkdir -p /var/interlegis/.virtualenvs

* Ajustar as permissões - onde sapl31 trocar por usuario::

    sudo chown -R sapl31:sapl31 /var/interlegis/


* Edite o arquivo ``.bashrc`` e adicione ao seu final as configurações abaixo para o virtualenvwrapper::

    nano /home/sapl31/.bashrc

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=/var/interlegis/.virtualenvs
    export PROJECT_HOME=/var/interlegis
    source /usr/local/bin/virtualenvwrapper.sh


* Carregue as configurações do virtualenvwrapper::

    source /home/sapl31/.bashrc



Clonar o projeto do github, ou fazer um fork e depois clonar
------------------------------------------------------------

* Para apenas clonar do repositório do Interlegis::

    cd /var/interlegis
    git clone git://github.com/interlegis/sapl

* Para fazer um fork e depois clonar, siga as instruções em https://help.github.com/articles/fork-a-repo que basicamente são:

  * Criar uma conta no github - é gratuíto.
  * Acessar https://github.com/interlegis/sapl e clicar em **Fork**.

  Será criado um domínio pelo qual será possível **clonar, corrigir, customizar, melhorar, contribuir, etc**::

      cd /var/interlegis
      git clone git://github.com/[SEU NOME]/sapl

* As configurações e instruções de uso para o git estão espalhadas pela internet e possui muito coisa bacana. As tarefas básicas de git e suas interações com github são tranquilas de se aprender.


Criar o ambiente virtual de desenvolvimento para o SAPL
-------------------------------------------------------
* ::

    mkvirtualenv -a /var/interlegis/sapl -p python3 -r requirements/requirements.txt sapl

Instalação e configuração das dependências do projeto
-----------------------------------------------------

* **Acesse o terminal e entre no virtualenv**::

    workon sapl

* **Instalar dependências python**::

    pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt

* **Configurar Postgresql**::

   sudo -u postgres psql -c "CREATE ROLE sapl LOGIN ENCRYPTED PASSWORD 'sapl' NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;"

   sudo -u postgres psql -c "ALTER ROLE sapl VALID UNTIL 'infinity';"

   sudo -u postgres psql -c "CREATE DATABASE sapl WITH OWNER = sapl ENCODING = 'UTF8' TABLESPACE = pg_default LC_COLLATE = 'pt_BR.UTF-8' LC_CTYPE = 'pt_BR.UTF-8' CONNECTION LIMIT = -1 TEMPLATE template0;"

  * Obs: no ambiente de desenvolvimento, a role deve ter permissão para criar outro banco. Isso é usado pelos testes automatizados.
  * (caso você já possua uma instalação do postrgresql anterior ao processo de instalação do ambiente de desenvolvimento do SAPL em sua máquina e sábia como fazer, esteja livre para proceder como desejar, porém, ao configurar o arquivo ``.env`` no próximo passo, as mesmas definições deverão ser usadas)


* **Ajustar as permissões - onde $USER trocar por usuario**::

    eval $(echo "sudo chown -R $USER:$USER /var/interlegis/")



* **Configurar arquivo .env**::


Criação da `SECRET_KEY <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`_:


* **Criar o arquivo ``.env`` dentro da pasta /var/interlegis/sapl/sapl/.env**::

    nano /var/interlegis/sapl/sapl/.env

      DATABASE_URL = postgresql://USER:PASSWORD@HOST:PORT/NAME
      SECRET_KEY = Gere alguma chave e coloque aqui
      DEBUG = [True/False]
      EMAIL_USE_TLS = [True/False]
      EMAIL_PORT = [Insira este parâmetro]
      EMAIL_HOST = [Insira este parâmetro]
      EMAIL_HOST_USER = [Insira este parâmetro]
      EMAIL_HOST_PASSWORD = [Insira este parâmetro]
      DEFAULT_FROM_EMAIL = [Insira este parâmetro]
      SERVER_EMAIL = [Insira este parâmetro]

      SOLR_URL = '[Insira este parâmetro]'


    * Uma configuração mínima para atender os procedimentos acima seria::

        DATABASE_URL = postgresql://sapl:sapl@localhost:5432/sapl
        SECRET_KEY = 'cole aqui entre as aspas simples a chave gerada pelo comando abaixo'
        DEBUG = False
        EMAIL_USE_TLS = True
        EMAIL_PORT = 587
        EMAIL_HOST =
        EMAIL_HOST_USER =
        EMAIL_HOST_PASSWORD =
        DEFAULT_FROM_EMAIL =
        SERVER_EMAIL =



Rodar o comando abaixo, um detalhe importante, esse comando só funciona com o django extensions, mas ele já está presente no arquivo requirements/requirements.txt desse projeto::

    python manage.py generate_secret_key

Copie a chave que aparecerá, edite o arquivo .env e altere o valor do parâmetro SECRET_KEY.


* Posicionar-se no diretorio do Projeto::

    cd /var/interlegis/sapl


* Instalar as dependências do ``bower``::

    eval $(echo "sudo chown -R $USER:$USER /home/$USER/")
    ./manage.py bower install

* Atualizar e/ou criar as tabelas da base de dados para refletir o modelo da versão clonada::

   ./manage.py migrate

* Subir o servidor do django::

   ./manage.py runserver 0.0.0.0:8001

* Acesse o SAPL em::

   http://localhost:8001/

================================
Instruções para instalar o Solr
================================

Solr é a ferramenta utilizada pelo SAPL 3.1 para indexar documentos para que possa ser feita
a Pesquisa Textual.

Adicione ao final do arquivo ``.env`` o seguinte atributo:

``SOLR_URL = 'http://127.0.0.1:8983/solr'``

Dentro do diretório principal siga os seguintes passos::

   curl -LO https://archive.apache.org/dist/lucene/solr/4.10.2/solr-4.10.2.tgz
   tar xvzf solr-4.10.2.tgz
   cd solr-4.10.2
   cd example
   java -jar start.jar
   ./manage.py build_solr_schema --filename solr-4.10.2/example/solr/collection1/conf/schema.xml


Após isso, deve-se parar o servidor do Solr e restartar com ``java -jar start.jar``
este processo prende o prompt

**OBS: Toda vez que o código da pesquisa textual for modificado, os comandos de build_solr_schema e start.jar devem ser rodados, nessa mesma ordem.**




Instruções para criação do super usuário e de usuários de testes
===========================================================================

* Criar super usuário do django-contrib-admin (Será solicitado alguns dados para criação)::

   ./manage.py createsuperuser

* `Os perfis semânticos do SAPL <https://github.com/interlegis/sapl/blob/master/sapl/rules/__init__.py>`_ são fixos e atualizados a cada execução do comando::

   ./manage.py migrate

* Os perfis fixos não aceitam customização via admin, porém outros grupos podem ser criados. O SAPL não interferirá no conjunto de permissões definidas em grupos customizados e se comportará diante de usuários segundo seus grupos e suas permissões.

* Os usuários de testes de perfil são criados apenas se o SAPL estiver rodando em modo DEBUG=True. Todos com senha "interlegis", serão::

    operador_administrativo
    operador_protocoloadm
    operador_comissoes
    operador_materia
    operador_norma
    operador_sessao
    operador_painel
    operador_geral
