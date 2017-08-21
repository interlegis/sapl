#!/bin/bash

# QA fix: Use ese script para corrigir automaticamente vários
#  problemas de estilo e boas práticas no código.
#
# Sempre guarde suas mudanças de alguma forma antes de aplicar esse script,
# de modo que possa revisar cada alteração que ele fez.
# Uma forma simples de fazer isso é adicionando antes suas mudanças à
# "staging area" do git, com `git add .` e após usar o script `git diff`.

isort --recursive --skip='migrations' --skip='templates' --skip='ipython_log.py*' .
autopep8 --in-place --recursive . --exclude='migrations,ipython_log.py*'
