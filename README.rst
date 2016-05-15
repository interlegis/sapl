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

Instalar as seguintes dependências do sistema (Roteiro testado no Ubuntu 16.04 64bits)::
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

Criar virtualenv usando python 3 para o projeto.
--------------------------------------------------

* Para usar `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_, instale com::

    sudo pip install virtualenvwrapper

    mkdir ~/Envs

* Edite o arquivo .bashrc e adicione eu seu final as configurações abaixo para o virtualenvwrapper::

    export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
    export WORKON_HOME=$HOME/.virtualenvs
    export PROJECT_HOME=$HOME/Envs
    source /usr/local/bin/virtualenvwrapper.sh

* Saia do terminal e entre novamente para as configurações do virtualenvwrapper serem carregadas. Após isso crie o ambiente virtual de desenvolvimento para o SAPL::

    mkvirtualenv sapl

* Crie arquivo .project em ~/.virtualenv/sapl::

    echo "$HOME/Envs/sapl" > .project


Clonar o projeto do github, ou fazer um fork e depois clonar
------------------------------------------------------------

* Para apenas clonar do repositório do Interlegis::

    cd ~/Envs
    git clone git://github.com/interlegis/sapl
    exit

* Para fazer um fork e depois clonar, siga as instruções em https://help.github.com/articles/fork-a-repo que basicamente:

  * É necessário ter uma conta no github - é gratuíto.
  * Acessar https://github.com/interlegis/sapl e clicar em fork.
  * Será criado um domínio pelo qual será possível **clonar, corrigir, customizar, melhorar, contribuir, etc**::

      cd ~/Envs
      git clone git://github.com/[SEU NOME]/sapl
      exit

* As configurações e instruções de uso para o git estão espalhadas pela internet e possui muito coisa bacana. As tarefas básicas de git e suas interações com github são tranquilas de aprender.

Instalação e configuração das dependências do projeto
-----------------------------------------------------

* Acesse o terminal e entre no virtualenv (Esse procedimento será sempre necessário para iniciar qualquer contribuição)::

    workon sapl

* Instalar dependências ``python``::

    pip install -r requirements/dev-requirements.txt

* Configurar Postgresql:

  * Acessar Postrgresql para criar o banco ``sapl`` com a role ``sapl`` (caso você já possua uma instalação do postrgresql anterior ao processo de instalação do ambiente de desenvolvimento do SAPL em sua máquina e sábia como fazer, esteja livre para proceder como desejar::

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

* Configurar arquivo ``.env``:

  * Criação da SECRET_KEY

  * Criar arquivo ``.env`` na pasta ~/Envs/sapl/sapl/.env:


* Install bower dependencies (run on the project root)::

    ./manage.py bower install

* Either run ``./manage.py migrate`` (for an empty database) or restore a database dump.

* In ``sapl/sapl`` directory create one file called ``.env``. Write the following attributes in it:

  - DATABASE_URL = postgresql://USER:PASSWORD@HOST:PORT/NAME
  - SECRET_KEY = Generate some key and paste here
  - DEBUG = [True/False]
  - EMAIL_USE_TLS = [True/False]
  - EMAIL_PORT = [Set this parameter]
  - EMAIL_HOST = [Set this parameter]
  - EMAIL_HOST_USER = [Set this parameter]
  - EMAIL_HOST_PASSWORD = [Set this parameter]

`Generate your secret key here <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`_

Instructions for Translators
============================

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


Tests
-----

* Write tests for all the functionality you implement.

* Keep the test coverage near 100%.

* To run all tests activate your virtualenv and issue these commands
  **at the root of the repository**::

    py.test

* To run the tests with coverage issue the command::

    py.test --cov . --cov-report term --cov-report html && firefox htmlcov/index.html

* The first time you run the tests after a migration (``./manage.py migrate``) use the db recreation option.
  This needs to be done only once::

    py.test --create-db

Issues
------

* Open all issues about the current development version (3.1) at the
  `Github Issue Tracker <https://github.com/interlegis/sapl/issues>`_.

* You can file issues in either Portuguese or English (at least for the time being).
