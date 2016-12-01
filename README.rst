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
   `Instalação do Ambiente de Desenvolvimento <https://github.com/interlegis/sapl/blob/master/docs/instacao31.rst>`_


Instruções para Importação da base mysql 2.5
============================================
   `Importação da Base do SAPL 2.5 para SAPL 3.1 <https://github.com/interlegis/sapl/blob/master/docs/importacao_25_31.rst>`_


Instruções para Deploy
======================
   `Deploy SAPL com Nginx + Gunicorn <https://github.com/interlegis/sapl/blob/master/docs/deploy.rst>`_



Instruções para Tradução
========================
   `Instruções para Tradução <https://github.com/interlegis/sapl/blob/master/docs/traducao.rst>`_



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
