#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTANTE:
# Esse script precisa rodar em python 2
# e depende apenas do descrito no arquivo requiments.txt

import cStringIO
import hashlib
import mimetypes
import os
import sys
from collections import defaultdict
from contextlib import contextmanager
from functools import partial

import git
import magic
import pyaml
import yaml
from unipath import Path

import ZODB.DB
import ZODB.FileStorage
from ZODB.broken import Broken

EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'application/xml': '.xml',
    'text/xml': '.xml',
    'application/zip': '.zip',
    'image/jpeg': '.jpeg',
    'image/png': '.png',
    'image/gif': '.gif',
    'text/html': '.html',
    'text/rtf': '.rtf',
    'text/x-python': '.py',
    'text/plain': '.txt',
    'SDE-Document': '.xml',
    'image/tiff': '.tiff',
    'application/tiff': '.tiff',
    'audio/x-wav': '.wav',
    'video/mp4': '.mp4',
    'image/x-icon': '.ico',
    'application/vnd.oasis.opendocument.text-template': '.ott',

    # TODO rever...
    'text/richtext': '.rtf',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
    'text/x-unknown-content-type': '',
}


def br(obj):
    if isinstance(obj, Broken):
        return obj.__Broken_state__
    else:
        return obj


def guess_extension(fullname, buffer):
    mime = magic.from_buffer(buffer, mime=True)
    try:
        return EXTENSOES[mime]
    except KeyError as e:
        possibilidades = '\n'.join(
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)])
        msg = '''Extensão não conhecida para o arquivo: {}
            e mimetype: {}
            Algumas possibilidades são:
            {}
            Atualize o código do dicionário EXTENSOES!
            '''.format(fullname, mime, possibilidades)
        print(msg)
        raise Exception(msg, e)


def dump_file(doc, path, salvar):
    name = doc['__name__']
    fullname = os.path.join(path, name)

    # A partir daqui usamos dict.pop('...') nos __Broken_state__
    # para contornar um "vazamento" de memória que ocorre
    # ao percorrer a árvore de objetos
    #
    # Imaginamos que, internamente, o ZODB está guardando referências
    # para os objetos Broken criados e não conseguimos identificar como.
    #
    # Essa medida descarta quase todos os dados retornados
    # e só funciona na primeira passagem

    pdata = br(doc.pop('data'))
    if isinstance(pdata, str):
        # Retrocedemos se pdata ja eh uma str (necessario em Images)
        doc['data'] = pdata
        pdata = doc

    output = cStringIO.StringIO()
    while pdata:
        output.write(pdata.pop('data'))
        pdata = br(pdata.pop('next', None))
    salvar(fullname, output.getvalue())
    return name


def enumerate_by_key_list(folder, key_list, type_key):
    for entry in folder.get(key_list, []):
        id, meta_type = entry['id'], entry[type_key]
        obj = br(folder.get(id, None))
        yield id, obj, meta_type


enumerate_folder = partial(enumerate_by_key_list,
                           key_list='_objects', type_key='meta_type')

enumerate_properties = partial(enumerate_by_key_list,
                               key_list='_properties', type_key='type')


def enumerate_btree(folder):
    contagem_esperada = folder['_count'].value
    tree = folder['_tree']
    for contagem_real, (id, obj) in enumerate(tree.iteritems(), start=1):
        obj, meta_type = br(obj), type(obj).__name__
        yield id, obj, meta_type
    # verificação de consistência
    assert contagem_esperada == contagem_real


nao_identificados = defaultdict(list)


@contextmanager
def logando_nao_identificados():
    nao_identificados.clear()
    yield
    if nao_identificados:
        print('#' * 80)
        print('#' * 80)
        print(u'FORAM ENCONTRADOS ARQUIVOS DE FORMATO NÃO IDENTIFICADO!!!')
        print(u'REFAÇA A EXPORTAÇÃO\n')
        print(nao_identificados)
        print('#' * 80)
        print('#' * 80)


def dump_folder(folder, path, salvar, enum=enumerate_folder):
    name = folder['id']
    path = os.path.join(path, name)
    if not os.path.exists(path):
        os.makedirs(path)
    for id, obj, meta_type in enum(folder):
        dump = DUMP_FUNCTIONS.get(meta_type, '?')
        if dump == '?':
            nao_identificados[meta_type].append(path + '/' + id)
        elif dump:
            id_interno = dump(obj, path, salvar)
            assert id == id_interno
    return name


def decode_iso8859(obj):
    return obj.decode('iso8859-1') if isinstance(obj, str) else obj


def read_sde(element):

    def read_properties():
        for id, obj, meta_type in enumerate_properties(element):
            yield id, decode_iso8859(obj)

    def read_children():
        for id, obj, meta_type in enumerate_folder(element):
            assert meta_type in ['SDE-Document-Element',
                                 'SDE-Template-Element',
                                 'SDE-Template-Link',
                                 'SDE-Template-Attribute',
                                 'Script (Python)',
                                 ]
            if meta_type != 'Script (Python)':
                # ignoramos os scrips python de eventos dos templates
                yield {'id': id,
                       'meta_type': meta_type,
                       'dados': read_sde(obj)}

    data = dict(read_properties())
    children = list(read_children())
    if children:
        data['children'] = children
    return data


def save_as_yaml(path, name, obj, salvar):
    fullname = os.path.join(path, name)
    conteudo = yaml.safe_dump(obj, allow_unicode=True)
    salvar(fullname, conteudo)


def dump_sde(strdoc, path, salvar, tipo):
    id = strdoc['id']
    sde = read_sde(strdoc)
    save_as_yaml(path,  '{}.{}.yaml'.format(id, tipo), sde, salvar)
    return id


DUMP_FUNCTIONS = {
    'File': dump_file,
    'Image': dump_file,
    'Folder': partial(dump_folder, enum=enumerate_folder),
    'BTreeFolder2': partial(dump_folder, enum=enumerate_btree),
    'SDE-Document': partial(dump_sde, tipo='sde.document'),
    'StrDoc': partial(dump_sde, tipo='sde.document'),
    'SDE-Template': partial(dump_sde, tipo='sde.template'),

    # explicitamente ignorados
    'ZCatalog': None,
    'Dumper': None,
    'CachingPolicyManager': None,
}


def get_app(data_fs_path):
    storage = ZODB.FileStorage.FileStorage(data_fs_path, read_only=True)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    app = br(root['Application'])

    def close_db():
        db.close()

    return app, close_db


def find_sapl(app):
    for obj in app['_objects']:
        id, meta_type = obj['id'], obj['meta_type']
        if id.startswith('cm_') and meta_type == 'Folder':
            cm_zzz = br(app[id])
            sapl = br(cm_zzz.get('sapl', None))
            if sapl and 'sapl_documentos' in sapl and 'acl_users' in sapl:
                return sapl


def dump_propriedades(docs, path, salvar, encoding='iso-8859-1'):
    props_sapl = br(docs['props_sapl'])
    ids = [p['id'] for p in props_sapl['_properties']]
    props = {id: props_sapl[id] for id in ids}
    props = {id: p.decode(encoding) if isinstance(p, str) else p
             for id, p in props.items()}
    save_as_yaml(path, 'sapl_documentos/propriedades.yaml', props, salvar)


def dump_usuarios(sapl, path, salvar):
    users = br(br(sapl['acl_users'])['data'])
    users = {k: br(v) for k, v in users['data'].items()}
    save_as_yaml(path, 'usuarios.yaml', users, salvar)


def _dump_sapl(data_fs_path, destino, salvar):
    assert Path(data_fs_path).exists()
    app, close_db = get_app(data_fs_path)
    try:
        sapl = find_sapl(app)
        # extrai folhas XSLT
        dump_folder(br(sapl['XSLT']), destino, salvar)
        # extrai usuários com suas senhas e perfis
        dump_usuarios(sapl, destino, salvar)

        # extrai documentos
        docs = br(sapl['sapl_documentos'])
        with logando_nao_identificados():
            dump_folder(docs, destino, salvar)
            dump_propriedades(docs, destino, salvar)
    finally:
        close_db()


DIR_DADOS_MIGRACAO = Path('~/migracao_sapl/').expand()


def repo_execute(repo, cmd, *args):
    return repo.git.execute(cmd.split() + list(args))


def get_annex_hashes(repo):
    hashes = repo_execute(
        repo, 'git annex find', '--format=${keyname}\n', '--include=*')
    return {os.path.splitext(h)[0] for h in hashes.splitlines()}


def ajusta_extensao(fullname, conteudo):
    base, extensao = os.path.splitext(fullname)
    if extensao not in ['.xsl', '.xslt', '.yaml']:
        # não trocamos as extensões XSL, XSLT e YAML
        extensao = guess_extension(fullname, conteudo)
    return base + extensao


def build_salvar(repo):
    """Constroi função salvar que pula arquivos que já estão no annex
    """
    hashes = get_annex_hashes(repo)

    def salvar(fullname, conteudo):
        sha = hashlib.sha256()
        sha.update(conteudo)
        if sha.hexdigest() not in hashes:
            fullname = ajusta_extensao(fullname, conteudo)
            if os.path.exists(fullname):
                # destrava arquivo pré-existente (o conteúdo mudou)
                repo_execute(repo, 'git annex unlock', fullname)
            with open(fullname, 'w') as arq:
                arq.write(conteudo)
            print(fullname)

    return salvar


def dump_sapl(sigla):
    data_fs_path = DIR_DADOS_MIGRACAO.child('datafs',
                                            'Data_cm_{}.fs'.format(sigla))
    assert data_fs_path.exists(), 'Origem não existe: {}'.format(data_fs_path)
    nome_banco_legado = 'sapl_cm_{}'.format(sigla)
    destino = DIR_DADOS_MIGRACAO.child('repos', nome_banco_legado)
    destino.mkdir(parents=True)
    repo = git.Repo.init(destino)
    repo_execute(repo, 'git annex init')
    repo_execute(repo, 'git config annex.thin true')

    salvar = build_salvar(repo)
    _dump_sapl(data_fs_path, destino, salvar)

    # grava mundaças
    repo_execute(repo, 'git annex add sapl_documentos')
    repo.git.add(A=True)
    if 'master' not in repo.heads or repo.index.diff('HEAD'):
        # se de fato existe mudança
        repo.index.commit('Exporta documentos do zope')


if __name__ == "__main__":
    if len(sys.argv) == 2:
        sigla = sys.argv[1]
        dump_sapl(sigla)
    else:
        print('Uso: python exporta_zope <sigla>')
