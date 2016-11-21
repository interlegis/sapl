.. image:: https://travis-ci.org/interlegis/sapl.svg?branch=master
 :target: https://travis-ci.org/interlegis/sapl


***********************************************
SAPL - Sistema de Apoio ao Processo Legislativo
***********************************************

Esta página reúne informações úteis sobre o desenvolvimento atual do SAPL.

Isso significa que toda a informação aqui apresentada aplica-se apenas para a versão 3.1 e superior.


Para obter mais informações sobre o projeto como um todo e a versão de trabalho
atual do sistema (2.5), visite a página do `projeto na Interlegis wiki <https://colab.interlegis.leg.br/wiki/ProjetoSapl>`_.


Instalação do Ambiente de Desenvolvimento
=========================================

* Procedimento testado nos seguintes SO's:

  * `Ubuntu 16.04 64bits <https://github.com/interlegis/sapl/blob/master/README.rst>`_;

        * edite e incremente outros, ou ainda, crie outros readme's dentro do projeto para outros SO's e adicione o link aqui.

Instalar as seguintes dependências do sistema::
----------------------------------------------------------------------------------------

* ::

    sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config postgresql postgresql-contrib pgadmin3 python-psycopg2 \
    software-properties-common build-essential libxml2-dev libjpeg-dev \
    libmysqlclient-dev libssl-dev libffi-dev libxslt1-dev python3-setuptools curl

    sudo -i
    curl -sL https://deb.nodesource.com/setup_5.x | bash -
    exit
    sudo apt-get install nodejs

    sudo npm install npm -g
    sudo npm install -g bower

Instalar o virtualenv usando python 3 para o projeto.
-----------------------------------------------------

* Para usar `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_, instale com::

    sudo pip install virtualenvwrapper

    mkdir ~/Envs

* Edite o arquivo ``.bashrc`` e adicione ao seu final as configurações abaixo para o virtualenvwrapper::

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Envs
    source /usr/local/bin/virtualenvwrapper.sh

* Saia do terminal e entre novamente para que as configurações do virtualenvwrapper sejam carregadas.

Clonar o projeto do github, ou fazer um fork e depois clonar
------------------------------------------------------------

* Para apenas clonar do repositório do Interlegis::

    cd ~/Envs
    git clone git://github.com/interlegis/sapl

* Para fazer um fork e depois clonar, siga as instruções em https://help.github.com/articles/fork-a-repo que basicamente são:

  * Criar uma conta no github - é gratuíto.
  * Acessar https://github.com/interlegis/sapl e clicar em **Fork**.

  Será criado um domínio pelo qual será possível **clonar, corrigir, customizar, melhorar, contribuir, etc**::

      cd ~/Envs
      git clone git://github.com/[SEU NOME]/sapl

* As configurações e instruções de uso para o git estão espalhadas pela internet e possui muito coisa bacana. As tarefas básicas de git e suas interações com github são tranquilas de se aprender.


Criar o ambiente virtual de desenvolvimento para o SAPL
-------------------------------------------------------
* ::

    mkvirtualenv sapl -a $HOME/Envs/sapl -p /usr/bin/python3

Instalação e configuração das dependências do projeto
-----------------------------------------------------

* **Acesse o terminal e entre no virtualenv**::

    workon sapl

* **Instalar dependências python**::

    pip install -r requirements/dev-requirements.txt

* **Configurar Postgresql**:

  * Acessar Postrgresql para criar o banco ``sapl`` com a role ``sapl``::

      sudo su - postgres
      psql

      CREATE ROLE sapl LOGIN
        ENCRYPTED PASSWORD 'sapl'
        NOSUPERUSER INHERIT CREATEDB NOCREATEROLE NOREPLICATION;

      ALTER ROLE sapl VALID UNTIL 'infinity';

      CREATE DATABASE sapl
        WITH OWNER = sapl
             ENCODING = 'UTF8'
             TABLESPACE = pg_default
             LC_COLLATE = 'pt_BR.UTF-8'
             LC_CTYPE = 'pt_BR.UTF-8'
             CONNECTION LIMIT = -1;

      \q
      exit

  * Se você possui uma cópia da base de dados do SAPL, essa é a hora para restaurá-la.
  * Obs: no ambiente de desenvolvimento, a role deve ter permissão para criar outro banco. Isso é usado pelos testes automatizados.
  * (caso você já possua uma instalação do postrgresql anterior ao processo de instalação do ambiente de desenvolvimento do SAPL em sua máquina e sábia como fazer, esteja livre para proceder como desejar, porém, ao configurar o arquivo ``.env`` no próximo passo, as mesmas definições deverão ser usadas)

* **Configurar arquivo .env**:

  * Criação da `SECRET_KEY <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`_:

    É necessário criar um projeto fake para extrair uma chave SECRET_KEY::

        mkdir ~/Envs/temp
        cd ~/Envs/temp

        django-admin startproject sapl_temp

        grep SECRET_KEY sapl_temp/sapl_temp/settings.py

    Copie a linha que aparecerá, volte para a pasta do projeto SAPL e apague sua pasta temporária::

        cd ~/Envs/sapl
        rm -R ~/Envs/temp

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

        DATABASE_URL = postgresql://sapl:sapl@localhost:5432/sapl
        SECRET_KEY = 'Substitua esta linha pela copiada acima'
        DEBUG = True
        EMAIL_USE_TLS = True
        EMAIL_PORT = 587
        EMAIL_HOST =
        EMAIL_HOST_USER =
        EMAIL_HOST_PASSWORD =



* Instalar as dependências do ``bower``::

    ./manage.py bower install

* Atualizar e/ou criar as tabelas da base de dados para refletir o modelo da versão clonada::

   ./manage.py migrate

* Atualizar arquivos estáticos::

   ./manage.py collectstatic --noinput

* Subir o servidor do django::

   ./manage.py runserver

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


Instruções para Importação da base mysql 2.5
============================================

Criar um arquivo `sapl/legacy/.env` com o seguinte conteúdo (parametros de acesso ao banco 2.5)::

  DATABASE_URL = mysql://[usuario do mysql]:[senha do myuysql]@[host]:[porta]/[banco]

o conteúdo do arquivo será semelhante a isso::

  DATABASE_URL = mysql://sapl:sapl@localhost:3306/interlegis

Posteriormente rodar a seguinte sequencia de comandos::

   ./manage.py shell_plus --settings=sapl.legacy_migration_settings
   >>> %run sapl/legacy/migration.py
   >>> migrate()
   
   
Instruções para fazer o Deploy
==============================
   
Instalando o servidor web NGINX::

  sudo pip install nginx
  
  
Instalando o servidor de aplicativos dedicados chamado Gunicorn::

  sudo pip install gunicorn  


Preparando o NGINX
------------------
vi /etc/nginx/sites-available/sapl31::

   upstream ENDERECO_SITE {  
      server unix:~/sapl/gunicorn.sock fail_timeout=0;
   }

   server {

       listen   80;
       server_name ENDERECO_SITE;

       client_max_body_size 4G;

       access_log /var/log/nginx-access.log;
       error_log /var/log/nginx-error.log;

       location /static/ {
           alias   ~/sapl/collected_static/;
       }

       location /media/ {
           alias   ~/sapl/media/;
       }

       location / {
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header Host $http_host;
           proxy_redirect off;
           if (!-f $request_filename) {
               proxy_pass http://ENDERECO_SITE;
               break;
           }
       }

       # Error pages
       error_page 500 502 503 504 /500.html;
       location = /500.html {
           root ~/sapl/sapl/static/;
       }
   }


Criar link simbólico para ativar o site::

   sudo ln -s /etc/nginx/sites-available/sapl3.conf /etc/nginx/sites-enabled/sapl3



Preparando o Gunicorn
---------------------
Na raiz do Projeto sapl, existe o arquivo chamado gunicorn_start.sh
onde ~/ devem ser alterados pelos caminhos correspondentes.

Para definir o parametro NUM_WORKERS  utilize a seguinte fórmula: 2 * CPUs + 1.
Para uma máquina de CPU única o valor seria 3

Para dar Permissão de execução para o script::

   chmod u+x bin/gunicorn_start

Para rodar o gunicorn::
   
   ./~/.gunicorn_start.sh
   
  

Instruções para Tradução
========================

Nós utilizamos o `Transifex <https://www.transifex.com>`_  para gerenciar as traduções do projeto.
Se você deseja contribuir, por favor crie uma conta no site e peça para se juntar a nós em `Transifex SAPL Page <https://www.transifex.com/projects/p/sapl>`_.
Assim que for aceito, você já pode começar a traduzir.

Para integrar as últimas traduções ao projeto atual, siga estes passos:

* Siga as instruções em `Development Environment Installation`_.

* Instale `Transifex Client <http://docs.transifex.com/client/config/>`_.

Aviso:

   O Transifex Client armazena senhas em 'plain text' no arquivo ``~/.transifexrc``.

   Nós preferimos logar no site do Transifex por meio de redes sociais (GitHub, Google Plus, Linkedin) e modificar, frequentemente, a senha utilizada pelo client.

* `Pull translations <http://docs.transifex.com/client/pull/>`_  ou `push translations <http://docs.transifex.com/client/push/>`_  usando o client. Faça o Pull somente com o repositório vazio, isto é, faça o commit de suas mudanças antes de fazer o Pull de novas traduções.

* Execute o programa com ``.manage.py runserver`` e cheque o sistema para ver se as traduções tiveram efeito.

Nota:

  O idioma do browser é utilizado para escolher as traduções que devem mostradas.



Orientações gerais de implementação
===================================

Boas Práticas
--------------

* Utilize a língua portuguesa em todo o código, nas mensagens de commit e na documentação do projeto.

* Mensagens de commit seguem o padrão de 50/72 colunas. Comece toda mensagem de commit com o verbo no infinitivo. Para mais informações, clique nos links abaixo:

  - Http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
  - Http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting

* Mantenha todo o código de acordo com o padrão da PEP8 (sem exceções).

* Antes de todo ``git push``:

  - Execute ``git pull --rebase`` (quase sempre).
  - Em casos excepcionais, faça somente ``git pull`` para criar um merge.

* Antes de ``git commit``, sempre:

  - Execute ``./manage.py check``
  - Execute todos os testes com ``py.test`` na pasta raiz do projeto

* Em caso de Implementação de modelo que envolva a classe ``django.contrib.auth.models.User``, não a use diretamente, use para isso a função ``get_settings_auth_user_model()`` de ``sapl.utils``. Exemplo:

  - no lugar de ``owner = models.ForeignKey(User, ... )``
  - use ``owner = models.ForeignKey(get_settings_auth_user_model(), ... )``

  - Não use em qualquer modelagem futura, ``ForeignKey`` com ``User`` ou mesmo ``settings.AUTH_USER_MODEL`` sem o import correto que não é o do projeto e sim o que está em ``sapl.utils``, ou seja (``from django.conf import settings``)

    - em https://docs.djangoproject.com/en/1.9/topics/auth/customizing/#referencing-the-user-model é explicado por que ser dessa forma!

  - Já em qualquer uso em implementação de execução, ao fazer uma query, por exemplo:

    - não use ``django.contrib.auth.models.User`` para utilizar as caracteristicas do model, para isso, use esta função: django.contrib.auth.get_user_model()

  - Seguir esses passos simplificará qualquer customização futura que venha a ser feita na autenticação do usuários ao evitar correções de inúmeros import's e ainda, desta forma, torna a funcionalidade de autenticação reimplementável por qualquer outro projeto que venha usar partes ou o todo do SAPL.

Atenção:

    O usuário do banco de dados ``sapl`` deve ter a permissão ``create database`` no postgres para que os testes tenham sucesso

* Se você não faz parte da equipe principal, faça o fork deste repositório e envie pull requests.
  Todos são bem-vindos para contribuir. Por favor, faça uma pull request separada para cada correção ou criação de novas funcionalidades.

* Novas funcionalidades estão sujeitas a aprovação, uma vez que elas podem ter impacto em várias pessoas.
  Nós sugerimos que você abra uma nova issue para discutir novas funcionalidades. Elas podem ser escritas tanto em Português, quanto em Inglês.



Testes
------

* Escrever testes para todas as funcionalidades que você implementar.

* Manter a cobertura de testes próximo a 100%.

* Para executar todos os testes você deve entrar em seu virtualenv e executar este comando **na raiz do seu projeto**::

    py.test

* Para executar os teste de cobertura use::

    py.test --cov . --cov-report term --cov-report html && firefox htmlcov/index.html

* Na primeira vez que for executar os testes após uma migração (``./manage.py migrate``) use a opção de recriação da base de testes.
  É necessário fazer usar esta opção apenas uma vez::

    py.test --create-db

Issues
------

* Abra todas as questões sobre o desenvolvimento atual no `Github Issue Tracker <https://github.com/interlegis/sapl/issues>`_.

* Você pode escrever suas ``issues`` em Português ou Inglês (ao menos por enquanto).
