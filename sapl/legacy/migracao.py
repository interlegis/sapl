import subprocess
from getpass import getpass

import requests
from django.core import management
from sapl.legacy.migracao_dados import REPO, TAG_MARCO, gravar_marco, info, migrar_dados
from sapl.legacy.migracao_documentos import migrar_documentos
from sapl.legacy.migracao_usuarios import migrar_usuarios
from sapl.legacy.scripts.exporta_zope.variaveis_comuns import TAG_ZOPE
from sapl.legacy.scripts.verifica_diff import verifica_diff
from sapl.legacy_migration_settings import DIR_REPO, NOME_BANCO_LEGADO
from sapl.materia.models import Proposicao
from unipath import Path


def adornar_msg(msg):
    return "\n{1}\n{0}\n{1}".format(msg, "#" * len(msg))


def migrar(primeira_migracao=True, apagar_do_legado=False):
    if TAG_MARCO in REPO.tags:
        info("A migração já está feita.")
        return
    assert TAG_ZOPE in REPO.tags, adornar_msg(
        "Antes de migrar " "é necessário fazer a exportação de documentos do zope"
    )
    management.call_command("migrate")
    migracao_corretiva = not primeira_migracao
    if migracao_corretiva:
        gravar_marco("producao", versiona=False, gera_backup=False)
    fks_orfas = migrar_dados(primeira_migracao, apagar_do_legado)
    assert not fks_orfas, "Ainda existem FKs órfãs"
    migrar_usuarios(REPO.working_dir, primeira_migracao)
    migrar_documentos(REPO, primeira_migracao)
    gravar_marco()
    if migracao_corretiva:
        sigla = NOME_BANCO_LEGADO[-3:]
        verifica_diff(sigla)


def compactar_media():

    # tar de media/sapl
    print("Criando tar de media... ", end="", flush=True)
    arq_tar = DIR_REPO.child("{}.media.tar".format(NOME_BANCO_LEGADO))
    arq_tar.remove()
    subprocess.check_output(["tar", "cfh", arq_tar, "-C", DIR_REPO, "sapl"])
    print("SUCESSO")


PROPOSICAO_UPLOAD_TO = Proposicao._meta.get_field("texto_original").upload_to


def salva_conteudo_do_sde(proposicao, conteudo):
    caminho_relativo = PROPOSICAO_UPLOAD_TO(
        proposicao, "proposicao_sde_{}.xml".format(proposicao.pk)
    )
    caminho_absoluto = Path(REPO.working_dir, caminho_relativo)
    caminho_absoluto.parent.mkdir(parents=True)
    # ajusta caminhos para folhas de estilo
    conteudo = conteudo.replace(b'"XSLT/HTML', b'"/XSLT/HTML')
    conteudo = conteudo.replace(b"'XSLT/HTML", b"'/XSLT/HTML")
    with open(caminho_absoluto, "wb") as arq:
        arq.write(conteudo)
    proposicao.texto_original = caminho_relativo
    proposicao.save()


def scrap_sde(url, usuario, senha=None):
    if not senha:
        senha = getpass()

    # login
    session = requests.session()
    res = session.post(
        "{}?retry=1".format(url),
        {"__ac_name": usuario, "__ac_password": senha},
    )
    assert res.status_code == 200

    url_proposicao_tmpl = "{}/sapl_documentos/proposicao/{}/renderXML?xsl=__default__"
    total = Proposicao.objects.count()
    for num, proposicao in enumerate(Proposicao.objects.all()):
        pk = proposicao.pk
        url_proposicao = url_proposicao_tmpl.format(url, pk)
        res = session.get(url_proposicao)
        print(
            "pk: {} status: {} {} (progresso: {:.2%})".format(
                pk, res.status_code, url_proposicao, num / total
            )
        )
        if res.status_code == 200:
            salva_conteudo_do_sde(proposicao, res.content)


def tenta_correcao():
    from sapl.legacy.migracao_dados import ocorrencias

    gravar_marco("producao", versiona=False, gera_backup=False)
    migrar_dados()
    assert "fk" not in ocorrencias, "AINDA EXISTEM FKS ORFAS"
    gravar_marco(versiona=False, gera_backup=False)
    sigla = NOME_BANCO_LEGADO[-3:]
    verifica_diff(sigla)


def commit_ajustes():
    import git

    sigla = NOME_BANCO_LEGADO[-3:]

    ajustes = Path(
        f"/home/mazza/work/consulta_sapls/ajustes_pre_migracao/{sigla}.sql"
    ).read_file()
    assert ajustes.count("RESSUSCITADOS") <= 1

    consulta_sapl = git.Repo(f"/home/mazza/work/consulta_sapls")
    consulta_sapl.git.add(
        f"/home/mazza/work/consulta_sapls/ajustes_pre_migracao/{sigla}*"
    )
    if consulta_sapl.git.diff("--cached"):
        consulta_sapl.index.commit(f"Ajusta {sigla}")
