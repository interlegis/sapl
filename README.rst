.. image:: https://badge.waffle.io/interlegis/sapl.png?label=ready&title=Ready 
 :target: https://waffle.io/interlegis/sapl
 :alt: 'Stories in Ready'

***********************************************
SAPL - Legislative Process Support System
***********************************************

This page brings together useful information on the current development of
**SAPL - Sistema de Apoio ao Processo Legislativo** (Legislative Process Support System).

That means all information presented here applies only to **version 3.1** and greater.

For more information about the the project as a whole and the current working version of the system (2.5)
please visit the `project page at Interlegis wiki <https://colab.interlegis.leg.br/wiki/ProjetoSapl>`_.


Development Environment Installation
====================================

* Install the following system dependencies (command bellow for Ubuntu)::

    sudo apt-get install git python3-dev libpq-dev graphviz-dev graphviz \
    postgresql postgresql-contrib pgadmin3 python-psycopg2 nodejs npm

    sudo ln -s /usr/bin/nodejs /usr/bin/node

    sudo npm install -g bower

* Setup git, following the instructions in https://help.github.com/articles/set-up-git.

* Fork and clone this repository, following the instructions in https://help.github.com/articles/fork-a-repo.

* Create a virtualenv using python 3 for the project and activate it.
  If you use `virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/en/latest/install.html#basic-installation>`_::

    mkvirtualenv -p /usr/bin/python3 sapl

* Install python dependencies (run on the project root)::

    pip install -r requirements/dev-requirements.txt

* Install bower dependencies (run on the project root)::

    ./manage.py bower install

* Install `PostgreSQL <https://help.ubuntu.com/community/PostgreSQL>`_ if you haven't already.

* Create a ``sapl`` role with:

  - Password ``sapl``
  - The privilege ``can create databases``
  - A big expiration date (or infinite, using eg ``ALTER ROLE SAPL VALID UNTIL 'infinity';``)

* Create a database ``sapl`` with owner ``sapl``.

* Either run ``./manage.py migrate`` (for an empty database) or restore a database dump.

* In sapl/sapl directory create one file called ``.env``. Write the following attribuitions
in it:

DATABASE_URL = postgresql://USER:PASSWORD@HOST:PORT/NAME
SECRET_KEY = Generate some key and paste here. You generate it using the link below.
DEBUG = [True/False]
EMAIL_USE_TLS = [True/False]
EMAIL_PORT = [Set this parameter]
EMAIL_HOST = [Set this parameter]
EMAIL_HOST_USER = [Set this parameter]
EMAIL_HOST_PASSWORD = [Set this parameter]

`Generate your secret key here <https://docs.djangoproject.com/es/1.9/ref/settings/#std:setting-SECRET_KEY>`

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
