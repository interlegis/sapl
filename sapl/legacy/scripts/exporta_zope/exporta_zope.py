#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTANTE:
# Esse script precisa rodar em python 2
# e depende apenas do descrito no arquivo requiments.txt

import os.path
import sys
from collections import defaultdict
from contextlib import contextmanager
from functools import partial
from os.path import splitext

import yaml

import ZODB.DB
import ZODB.FileStorage
from ZODB.broken import Broken

EXTENSOES = {
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
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


extensoes_desconhecidas = defaultdict(list)


def dump_file(doc, path):
    id = doc['__name__']
    name, extension = splitext(id)
    content_type = doc['content_type']
    extension = extension or EXTENSOES.get(content_type, '.ZZZ')

    fullname = os.path.join(path, name + extension)
    print(fullname)

    if extension == '.ZZZ':
        extensoes_desconhecidas[content_type].append(fullname)

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

    with open(fullname, 'w') as arq:
        while pdata:
            arq.write(pdata.pop('data'))
            pdata = br(pdata.pop('next', None))

    return id


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


def dump_folder(folder, path='', enum=enumerate_folder):
    name = folder['id']
    path = os.path.join(path, name)
    if not os.path.exists(path):
        os.makedirs(path)
    for id, obj, meta_type in enum(folder):
        dump = DUMP_FUNCTIONS.get(meta_type, '?')
        if dump == '?':
            nao_identificados[meta_type].append(path + '/' + id)
        elif dump:
            id_interno = dump(obj, path)
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
                yield id, read_sde(obj)

    data = dict(read_properties())
    children = list(read_children())
    if children:
        data['children'] = children
    return data


def save_as_yaml(path, name, obj):
    fullname = os.path.join(path, name)
    with open(fullname, 'w') as arquivo:
        yaml.safe_dump(obj, arquivo)
    print(fullname)
    return fullname


def dump_sde(strdoc, path, tipo):
    id = strdoc['id']
    sde = read_sde(strdoc)
    save_as_yaml(path,  '{}.{}.yaml'.format(id, tipo), sde)
    return id


DUMP_FUNCTIONS = {
    'File': dump_file,
    'Image': dump_file,
    'Folder': partial(dump_folder, enum=enumerate_folder),
    'BTreeFolder2': partial(dump_folder, enum=enumerate_btree),
    'SDE-Document': partial(dump_sde, tipo='sde.document'),
    'SDE-Template': partial(dump_sde, tipo='sde.template'),

    # explicitamente ignorados
    'ZCatalog': None,
    'Dumper': None,
}


def get_app(data_fs_path):
    storage = ZODB.FileStorage.FileStorage(data_fs_path)
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


def dump_propriedades(docs, path):
    props_sapl = br(docs['props_sapl'])
    ids = [p['id'] for p in props_sapl['_properties']]
    props = {id: props_sapl[id] for id in ids}
    props = {id: p.decode('iso-8859-1') if isinstance(p, str) else p
             for id, p in props.items()}
    save_as_yaml(path, 'sapl_documentos/propriedades.yaml', props)


def dump_usuarios(sapl, path):
    users = br(br(sapl['acl_users'])['data'])
    users = {k: br(v) for k, v in users['data'].items()}
    save_as_yaml(path, 'usuarios.yaml', users)


def dump_sapl(data_fs_path, destino='../../../../media'):
    app, close_db = get_app(data_fs_path)
    try:
        sapl = find_sapl(app)
        # extrai folhas XSLT
        dump_folder(br(sapl['XSLT']), destino)
        # extrai usuários com suas senhas e perfis
        dump_usuarios(sapl, destino)

        # extrai documentos
        docs = br(sapl['sapl_documentos'])
        with logando_nao_identificados():
            dump_folder(docs, destino)
            dump_propriedades(docs, destino)
    finally:
        close_db()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        data_fs_path = sys.argv[1]
        dump_sapl(data_fs_path)
    else:
        print('Uso: python exporta_zope <caminho p Data.fs>')
