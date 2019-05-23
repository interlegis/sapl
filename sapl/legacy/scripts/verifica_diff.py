import os
import subprocess

import yaml
from unipath import Path


def call(cmd):
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
    res.stdout = res.stdout.decode("utf-8")
    return res


def verifica_diff(sigla):
    repo = f"~/migracao_sapl/repos/sapl_cm_{sigla}"

    cd = f"cd {repo}"
    diff_cmd = f"{cd}; diff -rq producao dados"
    print(repo)

    out = call(
        f"{diff_cmd} | grep -v 'Files producao/sequences.yaml and dados/sequences.yaml differ' | tee ~/migracao_sapl/diffs/{sigla}.diff"
    ).stdout.splitlines()  # noqa

    assert all(o.startswith("Only in dados") for o in out)
    verifica_sequences(sigla)
    return out


def verifica_sequences(sigla):
    repo = f"~/migracao_sapl/repos/sapl_cm_{sigla}"

    sequences_producao, sequences_dados = [
        yaml.safe_load(
            Path(f"{repo}/{base}/sequences.yaml").expand_user().read_file()
        )
        for base in ("producao", "dados")
    ]
    # as sequences novas devem ter valores maiores ou iguais aos da producao
    assert all(
        sequences_dados[seq] >= sequences_producao[seq]
        for seq in sequences_producao
    )
