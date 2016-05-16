.. image:: https://badge.waffle.io/interlegis/sapl.png?label=ready&title=Ready
 :target: https://waffle.io/interlegis/sapl
 :alt: 'Stories in Ready'

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

    sudo apt-get install git nginx python3-dev libpq-dev graphviz-dev graphviz \
    pkg-config postgresql postgresql-contrib pgadmin3 python-psycopg2 \
    software-properties-common build-essential libxml2-dev libjpeg-dev \
    libssl-dev libffi-dev libxslt1-dev python3-setuptools curl

    sudo easy_install3 pip lxml

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

* **Instalar dependências ``python``**::

    pip install -r requirements/dev-requirements.txt

* **Configurar Postgresql**:

  * Acessar Postrgresql para criar o banco ``sapl`` com a role ``sapl``::

      sudo su - postgres

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

  * Se você possui uma cópia da base de dados do SAPL, essa é a hora para restaurá-la.
  * Obs: no ambiente de desenvolvimento, a role deve ter permissão para criar outro banco. Isso é usado pelos testes automatizados.
  * (caso você já possua uma instalação do postrgresql anterior ao processo de instalação do ambiente de desenvolvimento do SAPL em sua máquina e sábia como fazer, esteja livre para proceder como desejar, porém, ao configurar o arquivo ``.env`` no próximo passo, as mesmas definições deverão ser usadas)

* **Configurar arquivo ``.env``**:

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
      EMAIL_PORT = [Set this parameter]
      EMAIL_HOST = [Set this parameter]
      EMAIL_HOST_USER = [Set this parameter]
      EMAIL_HOST_PASSWORD = [Set this parameter]

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

* Atualizar e/ou criar a base de dados para refletir o modelo da versão clonada::

   ./manage.py migrate

* Atualizar arquivos estáticos::

   ./manage.py collectstatic --noinput

* Subir o servidor do django::

   ./manage.py runserver

* Acesse o SAPL em::

   http://localhost:8000/

Instruções para Tradução
========================

We use `Transifex <https://www.transifex.com>`_  to manage the project's translations.
If you want to contribute, please setup an account there and request to join us at
the `Transifex SAPL Page <https://www.transifex.com/projects/p/sapl>`_.
Once your join request is accepted, you can start to translate.

To integrate the last translations on a working instance follow these steps:

* Follow the instructions at `Development Environment Installation`_.

* Install `Transifex Client <http://docs.transifex.com/client/config/>`_.

.. warning::
   The Transifex Client stores passwords in plain text on the file ``~/.transifexrc``.

   We personally prefer to log into Transifex website with social network credentials and change the password used for the client frequently.

* `Pull translations <http://docs.transifex.com/client/pull/>`_  or `push translations <http://docs.transifex.com/client/push/>`_  using the client. Pull only on a clean repo, i.e. commit your changes before pulling new translations.

* Run the program with ``.manage.py runserver`` and check the system to see the translations into effect.

.. note::
  The browser language preference is used to choose the translations to display.


General implementation guidelines
=================================

Best practices
--------------

* Use English for all the code, commit messages and project docs.

* Commit messages following the standard 50/72 columns. Start every commit message with a verb in infinitive. For more info on this please check:

  - Http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
  - Http://stackoverflow.com/questions/2290016/git-commit-messages-50-72-formatting

* Keep all code in standard PEP8 (without exceptions).

* Before every ``git push``:
  - Run ``git pull --rebase`` (almost always).
  - In exceptional cases simply use ``git pull`` to produce a merge.

* Before ``git commit``, always:
  - Run ``./manage.py check``
  - Run all tests with ``py.test`` at the root of the project tree

.. attention::
    The database user ``sapl`` needs to have the permission ``create database`` in postgres for the tests to complete successfully

* If you're not part of the core team, fork the repo and submit pull requests.
  All are welcome to contribute. Please make a separate pull request for each bugfix/new feature.

* New features are subject to approval, since they may impact a lot of people.
  We suggest you open an issue to discuss new features. That can be made in Portuguese, as well as in English.


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
