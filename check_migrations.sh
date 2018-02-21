#!/bin/bash

falha ()
{
    NC='\033[0m'
    RED='\033[0;31m'
    echo
    echo -e "${RED}ALGUMAS ALTERAÇÕES EXIGEM MIGRAÇÃO.${NC}"
    echo -e "${RED}RODE 'python manage.py makemigrations' ANTES DE SUBMETER SEU CÓDIGO...${NC}"
    echo -e "${RED}lembre de adicionar os arquivos criados ao git com 'git add .' ou semelhante.${NC}"
    echo
    exit 1
}

# se há algum model no commit
if git diff --cached --name-status | grep -q '^M.*models\.py$'; then
  # deve haver alguma migration nova no commit
  if ! git diff --cached --name-status | grep -q '^A.*/migrations/[[:digit:]]\{4\}_.*\.py$'; then
    falha
  fi
fi

# a verificação de migrations pendentes deve passar

# TODO: Após migrar para Django 1.10 usar
#
#       ./manage.py makemigrations --check --dry-run
#
# ATENÇÃO: a chamada atual termina com exit 1 se NÃO HÁ migração a ser aplicada
#          ou seja, termina com "erro" se está tudo bem!
#          A chamada do django 1.10 INVERTE ISSO.
#
# https://docs.djangoproject.com/en/1.10/ref/django-admin/#cmdoption-makemigrations-check
if python manage.py makemigrations --dry-run --exit > /dev/null; then
  falha
fi