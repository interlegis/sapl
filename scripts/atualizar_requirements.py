#!/usr/bin/env python

# Este script altera os arquivos requirements/*requirements.txt
# atualizando as versões fixadas neles para coincidirem com as do venv.
#
# Rode esse script após atualizar as dependências do venv usando, p. ex.:
# pip-review
#
# Após usá-lo confira sempre o resultado com `git diff` e teste as mudanças

import glob
import re
import subprocess

freeze_output = subprocess.Popen(
    'pip freeze', shell=True,
    stdout=subprocess.PIPE).stdout.read().decode('ascii')
freeze = freeze_output.strip().split('\n')
freeze = {name.lower(): version
          for name, version in [re.split('==+', s) for s in freeze]}
req_files = glob.glob('requirements/*requirements.txt')
requirements = [(f, open(f).read().strip().split('\n'))
                for f in req_files]


def novas_linhas(linhas):
    for linha in linhas:
        split = re.split('==', linha)
        if len(split) == 1:
            yield split[0]
        else:
            nome, versao = split
            nome = nome.lower()
            yield '%s==%s' % (nome, freeze[nome])

for arq, linhas in requirements:
    with open(arq, 'w') as f:
        f.writelines(l + '\n' for l in novas_linhas(linhas))
