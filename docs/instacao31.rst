Instalação do Ambiente de Desenvolvimento
=========================================

* Procedimento testado nos seguintes SO's:

  * `Ubuntu 16.04 64bits <https://github.com/interlegis/sapl/blob/master/README.rst>`_;

* Para esta instalação foi utilizado o usuário de sistema sapl31


Atualizar o sistema
-------------------

  sudo apt-get update
  sudo apt-get upgrade



Instalar as seguintes dependências do sistema::
----------------------------------------------------------------------------------------

* ::

    sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config postgresql postgresql-contrib pgadmin3 python-psycopg2 \
    software-properties-common build-essential libxml2-dev libjpeg-dev \
    libmysqlclient-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools \
    python3-pip curl

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
    
* Ajustar as permissões - onde sapl31 trocar por usuario    
    sudo chown -R sapl31:sapl31 /var/interlegis/
        

* Edite o arquivo ``.bashrc`` e adicione ao seu final as configurações abaixo para o virtualenvwrapper::
    
    nano /home/sapl31/.bashrc    
    
    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=/var/interlegis/.virtualenvs
    export PROJECT_HOME=/var/interlegis
    source /usr/local/bin/virtualenvwrapper.sh

* Carregue as configurações do virtualenvwrapper.
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

    mkvirtualenv sapl -a /var/interlegis/sapl -p /usr/bin/python3

Instalação e configuração das dependências do projeto
-----------------------------------------------------

* **Acesse o terminal e entre no virtualenv**::

    workon sapl

* **Instalar dependências python**::

    pip install -r /var/interlegis/sapl/requirements/dev-requirements.txt

* **Configurar Postgresql**:

sudo -u postgres psql -c "CREATE ROLE sapl LOGIN ENCRYPTED PASSWORD 'sapl' NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;"
sudo -u postgres psql -c "ALTER ROLE sapl VALID UNTIL 'infinity';"
sudo -u postgres psql -c "CREATE DATABASE sapl WITH OWNER = sapl ENCODING = 'UTF8' TABLESPACE = pg_default LC_COLLATE = 'pt_BR.UTF-8' LC_CTYPE = 'pt_BR.UTF-8' CONNECTION LIMIT = -1;"

  * Se você possui uma cópia da base de dados do SAPL, essa é a hora para restaurá-la.
  * Obs: no ambiente de desenvolvimento, a role deve ter permissão para criar outro banco. Isso é usado pelos testes automatizados.
  * (caso você já possua uma instalação do postrgresql anterior ao processo de instalação do ambiente de desenvolvimento do SAPL em sua máquina e sábia como fazer, esteja livre para proceder como desejar, porém, ao configurar o arquivo ``.env`` no próximo passo, as mesmas definições deverão ser usadas)

* **Configurar arquivo .env**:

  * Criação da `SECRET_KEY <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`_:

    É necessário criar um projeto fake para extrair uma chave SECRET_KEY::

        mkdir /var/interlegis/temp
        cd /var/interlegis/temp

        django-admin startproject sapl_temp

        grep SECRET_KEY sapl_temp/sapl_temp/settings.py

    Copie a linha que aparecerá, volte para a pasta do projeto SAPL e apague sua pasta temporária::

        cd /var/interlegis/
        rm -R /var/interlegis/temp
        
* Ajustar as permissões - onde sapl31 trocar por usuario    
    sudo chown -R sapl31:sapl31 /var/interlegis/

  * Criar o arquivo ``.env`` dentro da pasta ~/Envs/sapl/sapl/.env::

DATABASE_URL = postgresql://USER:PASSWORD@HOST:PORT/NAME
      SECRET_KEY = Gere alguma chave e coloque aqui
      DEBUG = [True/False]
      EMAIL_USE_TLS = [True/False]
      EMAIL_PORT = [Insira este parâmetro]
      EMAIL_HOST = [Insira este parâmetro]
      EMAIL_HOST_USER = [Insira este parâmetro]
      EMAIL_HOST_PASSWORD = [Insira este parâmetro]

    * Uma configuração mínima para atender os procedimentos acima seria::
  
  nano /var/interlegis/sapl/sapl/.env
  
        DATABASE_URL = postgresql://sapl:sapl@localhost:5432/sapl
        SECRET_KEY = 'Substitua esta linha pela copiada acima'
        DEBUG = True
        EMAIL_USE_TLS = True
        EMAIL_PORT = 587
        EMAIL_HOST =
        EMAIL_HOST_USER =
        EMAIL_HOST_PASSWORD =


cd /var/interlegis/sapl

* Instalar as dependências do ``bower``::

    ./manage.py bower install

* Atualizar e/ou criar as tabelas da base de dados para refletir o modelo da versão clonada::

   ./manage.py migrate

* Atualizar arquivos estáticos::

   ./manage.py collectstatic --noinput

* Subir o servidor do django::

   ./manage.py runserver 0.0.0.0:8001

* Acesse o SAPL em::

   http://localhost:8000/

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
