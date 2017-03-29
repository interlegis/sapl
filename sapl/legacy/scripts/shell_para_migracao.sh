#!/bin/bash

# Inicia um shell_plus com as configurações de migração usando um banco específico
# Uso: ./shell_para_migracao.sh <NOME DO BANCO>

# Rode esse script a partir da raiz do projeto

DATABASE_NAME=$1 ./manage.py shell_plus --settings sapl.legacy_migration_settings
