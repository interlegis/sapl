#!/bin/bash

verifica_git() {
  if [[ ! -d ".git" ]]; then
    echo -e "\033[31mERRO\033[0m  Diretório atual não é um repositório git!"
    exit 1
  fi
}

verifica_diretorio() {
  DIR=$(pwd | rev | cut -d'/' -f1 | rev)

  if [[ "$DIR" != "$1" ]]; then
    echo -e "\033[31mERRO\033[0m  Diretório atual não é o \033[1m$1\033[0m!"
    exit 1
  fi

  verifica_git
}

retorna_branch() {
  # shellcheck disable=SC2155
  local branch=$(git branch | grep '^*' | cut -d ' ' -f2)
  if [[ -z "$branch" ]]; then
    echo -e "\033[31mERRO\033[0m  Não foi possivel configurar a variável \033[1m$1\033[0m!"
    exit 1
  else
    echo "$branch"
  fi
}

if [[ ! (( "$1" == "build" ) || ( "$1" == "serve" )) ]]; then
  echo -e "\033[31mERRO\033[0m  Parâmetro inválido!"
  echo -e "      Coloque \033[1mbuild\033[0m ou \033[1mserve\033[0m."
  exit 1
fi

verifica_diretorio "sapl-frontend"

BRANCH_FRONTEND="$(retorna_branch "BRANCH_FRONTEND")"

# shellcheck disable=SC2164
cd ../sapl > /dev/null 2>&1
if [[ ! $? -eq 0 ]]; then
   echo "\033[31mERRO\033[0m  Os diretórios \033[1msapl\033[0m e \033[1msapl-frontend\033[0m devem ter o mesmo diretório raiz."
   exit 1
fi

verifica_diretorio "sapl"

BRANCH_BACKEND="$(retorna_branch "BRANCH_BACKEND")"

cd ../sapl-frontend > /dev/null 2>&1

if [[ "$BRANCH_FRONTEND" == "$BRANCH_BACKEND" ]]; then
  echo -e "\033[33mEXECUTANDO\033[0m  \033[1myarn run $1\033[1m."
  yarn run "$1"
  echo -e "\033[32mSUCESSO\033[0m  $1 realizado com sucesso."
else
  echo -e "\033[31mERRO\033[0m  $1 não realizada porque as branchs dos dois repositórios são diferentes."
  echo -e "      Branch do Frontend:   \033[1m$BRANCH_FRONTEND\033[0m"
  echo -e "      Branch do Backend:    \033[1m$BRANCH_BACKEND\033[0m"
  echo -e "      Para que a operação seja feita, coloque os dois repositórios na mesma branch."
fi
