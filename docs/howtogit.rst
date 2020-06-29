====
De forma muito simples e em linhas gerais o básico sobre Git
====

Glosário
---------

  Git - Sistema de controle de versão de aquivos
  
  GitHub - É um serviço web que oferece diversas funcionalidades extras aplicadas ao Git
 
  Branch - Significa ramificar seu projeto, criar um snapshot
  
  Merge - Significa incorporar seu branch ao master


Pode ser útil
-------------

Atualizar a base local:
  
  git pull --rebase git://github.com/interlegis/sapl

Exibir informações:

  git status
 
Ver repositório:
  
  git remote -v

Definir repositório:

  git remote set-url origin https://github.com/interlegis/sapl.git

Criar um branch:
  
  git checkout -b nome_branch
  git add arquivos

Remover um branch:

  git branch -d nome-branch

Commitar:

  git commit -m "Comentário"

Enviar o branch:
  
  git push origin nome_branch

Na base local, descartar alguma alteração feita nos arquivos:

  git checkout -- <arquivo>
  
Ao invés disso, remover todas as alterações e commits locais, recuperar o histórico mais recente do servidor e apontar para seu branch master local:
  
  git fetch origin
  git reset --hard origin/master

Atualizar para algum branch específico (ex:785-atualizar-migracao):

  git checkout 785-atualizar-migracao

Voltar para a branch master:
  
  git checkout master

Verificar os últimos 5 commits:

  git log --oneline -n 5
 
  
Referência:
  
    http://rogerdudler.github.io/git-guide/index.pt_BR.html
    http://tableless.com.br/tudo-que-voce-queria-saber-sobre-git-e-github-mas-tinha-vergonha-de-perguntar/
