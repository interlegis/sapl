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

::

    sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config postgresql postgresql-contrib pgadmin3 python-psycopg2 \
    software-properties-common build-essential libxml2-dev libjpeg-dev \
    libmysqlclient-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools \
    python3-pip poppler-utils antiword default-jre python3-venv

Instalar o virtualenv usando python 3 para o projeto.
-----------------------------------------------------

* Para usar `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_, instale com::

    sudo pip3 install virtualenvwrapper

    sudo mkdir -p /var/interlegis/.virtualenvs

* Ajustar as permissões::

    sudo chown -R $USER:$USER /var/interlegis/


* Edite o arquivo ``.bashrc`` e adicione ao seu final as configurações abaixo para o virtualenvwrapper::

    nano /home/$USER/.bashrc

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=/var/interlegis/.virtualenvs
    export PROJECT_HOME=/var/interlegis
    source /usr/local/bin/virtualenvwrapper.sh


* Carregue as configurações do virtualenvwrapper::

    source /home/$USER/.bashrc



Clonar o projeto do github, ou fazer um fork e depois clonar
------------------------------------------------------------

* Para apenas clonar do repositório do Interlegis::

    cd /var/interlegis

    git clone -b 3.1.x --single-branch git://github.com/interlegis/sapl

    O comando acima irá clonar a última versão estável do SAPL (3.1.x)
    Para clonar todo o repositório utilize o comando abaixo:

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
::

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


* **Ajustar as permissões - onde $USER trocar por usuário**::

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
      EMAIL_SEND_USER = [Insira este parâmetro]
      EMAIL_HOST_PASSWORD = [Insira este parâmetro]
      DEFAULT_FROM_EMAIL = [Insira este parâmetro]
      SERVER_EMAIL = [Insira este parâmetro]

      SOLR_URL = '[Insira este parâmetro]'
      USE_SOLR = '[Insira este parâmetro]'
      SOLR_COLLECTION = '[Insira este parâmetro]'
      
      FRONTEND_CUSTOM = [True/False]

      USE_CHANNEL_LAYERS = True
      HOST_CHANNEL_LAYERS: localhost
      PORT_CHANNEL_LAYERS: 6379

      SITE_URL = '[Insira este parâmetro]'

      TZ = 'America/Sao_Paulo'

    * Uma configuração mínima para atender os procedimentos acima seria::

        DATABASE_URL = postgresql://sapl:sapl@localhost:5432/sapl
        SECRET_KEY = 'cole aqui entre as aspas simples a chave gerada pelo comando abaixo'
        DEBUG = True


Rodar o comando abaixo, um detalhe importante, esse comando só funciona com o django extensions, mas ele já está presente no arquivo requirements/requirements.txt desse projeto::

    python manage.py generate_secret_key

Copie a chave que aparecerá, edite o arquivo .env e altere o valor do parâmetro SECRET_KEY.


* Posicionar-se no diretorio do Projeto::

    cd /var/interlegis/sapl

* Atualizar e/ou criar as tabelas da base de dados para refletir o modelo da versão clonada::

   ./manage.py migrate

* Subir o servidor do django::

   ./manage.py runserver 0.0.0.0:8001

* Acesse o SAPL em::

   http://localhost:8001/

Instruções para criação do super usuário e de usuários de testes
===========================================================================

* Criar super usuário do django-contrib-admin (Será solicitado alguns dados para criação)::

   python3 manage.py createsuperuser

* `Os perfis semânticos do SAPL <https://github.com/interlegis/sapl/blob/master/sapl/rules/__init__.py>`_ são fixos e atualizados a cada execução do comando::

   ./manage.py migrate

* Os perfis fixos não aceitam customização via admin, porém outros grupos podem ser criados. O SAPL não interferirá no conjunto de permissões definidas em grupos customizados e se comportará diante de usuários segundo seus grupos e suas permissões.

* Para criar os usuários de teste, deve-se seguir os seguintes passos::

    ./manage.py shell_plus
    from sapl.rules.apps import cria_usuarios_padrao
    cria_usuarios_padrao()


* Todos com senha "interlegis", serão::

    operador_administrativo
    operador_protocoloadm
    operador_comissoes
    operador_materia
    operador_norma
    operador_sessao
    operador_painel
    operador_geral


Sapl-Frontend
=============

* O Sapl foi separado em outro projeto, o SAPL Frontend que está aqui no github, no repositório do Interlegis. Veja Aqui: https://github.com/interlegis/sapl-frontend::

* Se seu objetivo é preparar o ambiente de desenvolvimento para colaborar no backend, você não precisa se preocupar com o tutorial abaixo pois na pasta https://github.com/interlegis/sapl/tree/3.1.x/sapl/static já está o código oficial de produção exportado pelo projeto do Sapl-Frontend

* Para colaborar com o Sapl-Frontend ou fazer seu próprio frontend a partir do oficial, siga os passos abaixo:

Preparação do ambiente::
----------------------

* **Instalação do NodeJs LTS 10.15.x**::

    curl -sL https://deb.nodesource.com/setup_10.x | sudo -E bash -
    sudo apt-get install -y nodejs

* **Instalação do Yarn**::

    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
    sudo apt-get update && sudo apt-get install yarn

* **Instalação do Vue-Cli**::

    yarn global add @vue/cli


Ligando os projetos SAPL e Sapl-Frontend para implementação no Sapl-Frontend
-----------------------------------------------------------------------------

**É fundamental que o Sapl-Frontend esteja na mesma pasta que o Sapl**

* Como orientado acima, o Sapl foi clonado na pasta `/var/interlegis`. O mesmo deve ser feito com o sapl-frontend, ficando assim::


    /var/interlegis/sapl
    /var/interlegis/sapl-frontend


* para tal, execute::

    cd /var/interlegis    
    git clone git://github.com/interlegis/sapl-frontend
    
**Você pode também criar um Fork do sapl-frontend**

* Para fazer um fork e depois clonar, siga as instruções em https://help.github.com/articles/fork-a-repo que basicamente são:

  * Criar uma conta no github - é gratuíto.
  * Acessar https://github.com/interlegis/sapl-frontend e clicar em **Fork**.

* Será criado um domínio pelo qual será possível **clonar, corrigir, customizar, melhorar, contribuir, etc**::

      cd /var/interlegis
      git clone git://github.com/[SEU NOME]/sapl-frontend


Feito isso, e você ativando a variável de ambiente FRONTEND_CUSTOM=True (vide acima criação do .env), o Sapl (backend) desativa a pasta *static* no seu ambiente de desenvolvimento e no seu ambiente de produção e passa a valer para o Sapl (backend) o que você customizar em sapl-frontend. Resumindo:

* Se você está criando um fork do sapl-frontend para ter o sapl com sua cara, ou criando funcionalidades de seu interesse: 
    
    FRONTEND_CUSTOM=True

* Se você está colaborando com a evolução oficial do sapl-frontend e enviará seu código para o repositório oficial através de um PR e, por consequência, gerará novos versão de produção a ser colocada na pasta static, então:
    
    FRONTEND_CUSTOM=False

**Deste ponto em diante, é exigido o conhecimento que você pode adquirir em https://cli.vuejs.org/guide/ e em https://vuejs.org/v2/guide/ para colaborar com sapl-frontend**

**OBS: após a separação do sapl para o sapl-frontend, o conteúdo da pasta static é compilado e minificado. É gerado pelo build do sapl-frontend e não deve-se tentar customizar ou criar elementos manipulando diretamente informações na pasta static.**

Django-Channels
===============

Para ativar Django-Channels e a comunicação via websockets utilizada pelo entry-point sessao/online de sapl-frontend coloque no arquivo .env a variável:

    USE_CHANNEL_LAYERS = True
    HOST_CHANNEL_LAYERS: localhost
    PORT_CHANNEL_LAYERS: 6379


Ao ativar o channels, no ambiente de desenvolvimento é necessário ativar um servidor redis. Utilize/Instale o docker e execute:

  sudo docker run -p 6379:6379 -d redis:5.0.3-stretch

No caso de ambiente de produção, o container do docker sapl para produção já está configurado com redis.

Testes do channels
------------------

Existe uma interface mínima de comunicação para testes dentro do sapl. Pode ser acessada utilizando:

  http://localhost:8001/sapl/time-refresh/

Se clicar em `pull`, o websocket de teste deve responder:

  {"message": "OK"}

De outro modo, ficando com esta interface aberta, abra outra janela e altere/inclua/apague algo em seu sapl. Será enviado um json que segue este padrão:

  {"message": {"action": "post_save", "id": 16923, "app": "materia", "model": "autoria"}}

O papel de /sapl/time-refresh/ é apenas isto, informar que houve ação no registro `id`, da `app` e `model`. Além de `action` que pode ser `post_save` ou `pre-delete`.
