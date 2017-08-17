#!/bin/bash

python manage.py makemigrations --dry-run --exit

MIGRATIONS=$?

NC='\033[0m'

if [ $MIGRATIONS -eq 0 ]; then
	RED='\033[0;31m'
	echo -e "${RED}You have unapplied code changes. run 'python manage.py makemigrations' before submitting your code...${NC}"
	exit 1
else
	GREEN='\033[0;32m'
	echo -e "Working normally..."
	exit 0
fi