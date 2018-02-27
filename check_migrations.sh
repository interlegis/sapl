#!/bin/bash

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
    NC='\033[0m'
    RED='\033[0;31m'
    echo
    echo -e "${RED}ALGUMAS ALTERAÇÕES EXIGEM MIGRAÇÃO.${NC}"
    echo -e "${RED}RODE 'python manage.py makemigrations' ANTES DE SUBMETER SEU CÓDIGO...${NC}"
    echo -e "${RED}lembre de adicionar os arquivos criados ao git com 'git add .' ou semelhante.${NC}"
    echo
    exit 1
fi