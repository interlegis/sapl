.. image:: https://travis-ci.org/interlegis/sapl.svg?branch=3.1.x
 :target: https://travis-ci.org/interlegis/sapl


***********************************************
SAPL - Sistema de Apoio ao Processo Legislativo
***********************************************

UPDATE! [02/08/2022]: Novas alterações foram realizadas nos containers do SAPL e no docker-compose.yaml. Estas mudanças estarão funcionais a partir do próximo release. Enquanto isso não vem, continuem utilizando as versões antigas do docker-compose.yaml. 

~~**UPDATE! [16/05/2022]: Devido a refatorações recentes no Solr, foi necessårio
adaptar o uso deste pelo SAPL. Para isso foram feitas mudanças no docker-compose.yml
como a adição de um container para o ZooKeeper e upload de arquivo de segurança.
Recomendamos fortemente que para a versão 3.1.162 e superior do SAPL seja feito o backup do
Banco de Dados, limpeza dos containers no host (`sudo docker system prune -a -f --volumes`),
e consequente instalação dos novos containers a partir da execução do docker-compose. É
importante frisar que o comando `docker system prune` irá apagar TODOS os containers E
TODOS os volumes (incluindo o BD) do host. Após o inicio dos novos containers, proceda
com a restauração do BD, pare os containers e reinicie novamente para indexação textual.
Além disso, o docker-compose.yml foi movido para a pasta dist/ na raiz do projeto.**~~

Esta página reúne informações úteis sobre o desenvolvimento atual do SAPL.

Isso significa que toda a informação aqui apresentada aplica-se apenas para a versão 3.1 e superior.


Para obter mais informações sobre o projeto como um todo e a versão de trabalho
atual do sistema (2.5), visite a página do `projeto na Interlegis wiki <https://colab.interlegis.leg.br/wiki/ProjetoSapl>`_.


**IMPORTANTE:** A partir da versão 3.1.162 do SAPL, as funcionalidades de recuperar senha,
acompanhamento de matéria, e acompanhamento de documento exigirão o uso do `Google reCaptcha <https://www.google.com/recaptcha/>`_. Cada casa legislativa será responsável pela geração
das chaves do reCaptcha e configuração no SAPL em Sistema -> Tabelas Auxiliares -> Configurações da Aplicação.
Sem essa configuração não serão habilitados os recursos citados anteriormente.
Veja mais detalhes sobre o processo de geração de chaves e configuração neste link https://www.youtube.com/watch?v=6ZCCyBjSJ-c
e no caderno de exercícios do SAPL 3.1 disponível na `Wiki do projeto <https://colab.interlegis.leg.br/wiki/ProjetoSapl3.1>`_

Instalação do Ambiente de Desenvolvimento
=========================================
   `Instalação do Ambiente de Desenvolvimento <https://github.com/interlegis/sapl/blob/3.1.x/docs/instalacao31.rst>`_


Instalação do Solr
======================
   `Instalação e configuração do Solr <https://github.com/interlegis/sapl/blob/3.1.x/docs/solr.rst>`_


Instruções para Deploy
======================
   `Deploy SAPL com Nginx + Gunicorn <https://github.com/interlegis/sapl/blob/3.1.x/docs/deploy.rst>`_


Instruções para Importação da base mysql 2.5
============================================
   `Importação da Base do SAPL 2.5 para SAPL 3.1 <https://github.com/interlegis/sapl/wiki/Migra%C3%A7%C3%A3o-sapl-2.5-para-3.1>`_


Instruções para Tradução
========================
   `Instruções para Tradução <https://github.com/interlegis/sapl/blob/3.1.x/docs/traducao.rst>`_



Orientações gerais de implementação
===================================
   `Instruções para Implementação <https://github.com/interlegis/sapl/blob/3.1.x/docs/implementacoes.rst>`_



Orientações gerais sobre o GitHub
===================================
   `Instruções para GitHub <https://github.com/interlegis/sapl/blob/3.1.x/docs/howtogit.rst>`_



Perguntas Frequentes
===================================
   `Perguntas Frequentes <https://github.com/interlegis/sapl/wiki/Perguntas-Frequentes>`_




Issues
------

* Abra todas as questões sobre o desenvolvimento atual no `Github Issue Tracker <https://github.com/interlegis/sapl/issues>`_.

* Você pode escrever suas ``issues`` em Português ou Inglês (ao menos por enquanto).

