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
 
 
Ver repositorio
  
  git remote -v
  

Para definir repositorio

  git remote set-url origin https://github.com/interlegis/sapl.git


Para criar um branch
  
  git checkout -b nome_branch
  git add arquivos

Para remover um branch

  git branch -d nome-branch


Para comitar

  git commit -m "Comentário"

Para enviar o branch
  
  git push origin nome_branch


Na base local descartar alguma alteração feita nos arquivos:

  git checkout -- <arquivo>
  
  
Ao invés dissoremover todas as alterações e commits locais, recuperar o histórico mais recente do servidor e apontar para seu branch master local
  
  git fetch origin
  git reset --hard origin/master

Atualizar para alguma brach especifica (ex:785-atualizar-migracao):

  git checkout 785-atualizar-migracao

Voltar para a branch master
  
  git checkout master

Verificar 5 ultimos comits:

  git log --oneline -n 5
  
  
Referência:
  
    http://rogerdudler.github.io/git-guide/index.pt_BR.html
    http://tableless.com.br/tudo-que-voce-queria-saber-sobre-git-e-github-mas-tinha-vergonha-de-perguntar/
