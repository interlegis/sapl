De forma muito simples e em linhas gerais o básico sobre GIT

Glosário
---------

  Git - Sistema de controle de versão de aquivos
  
  GitHub - É um serviço web que oferece diversas funcionalidades extras aplicadas ao git
 
  Branch - Significa ramificar seu projeto, criar um snapshot.
  
  Merge - Significa incorporar seu branch no master


Pode ser útil
-------------

Atualizar a base local:
  
  git pull --rebase git://github.com/interlegis/sapl

Exibir informações:

  git status


Na base local descartar alguma alteração feita nos arquivos:

  git checkout sapl/legacy_migration_settings.py

Atualizar para alguma brach especifica (ex:785-atualizar-migracao):

  git checkout 785-atualizar-migracao

Voltar para a branch master
  
  git checkout master

Verificar 5 ultimos comits:

  git log --oneline -n 5
