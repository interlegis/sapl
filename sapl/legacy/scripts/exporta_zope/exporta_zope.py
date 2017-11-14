#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTANTE:
# Esse script precisa rodar em python 2
# e depende apenas do descrito no arquivo requiments.txt

import os.path
import sys
from collections import defaultdict
from functools import partial

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
    'SDE-Document': 'xml',

    # TODO rever...
    'text/richtext': '.rtf',

    # sem extensao
    'application/octet-stream': '',  # binario
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
    name = doc['__name__']
    content_type = doc['content_type']
    extension = EXTENSOES.get(content_type, 'ZZZZ')

    fullname = os.path.join(path, name + extension)
    print(fullname)

    if extension == 'ZZZZ':
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

    return name


def enumerate_folder(folder):
    # folder vazio nao tem _objects
    for entry in folder.get('_objects', []):
        id, meta_type = entry['id'], entry['meta_type']
        obj = br(folder[id])
        yield id, obj, meta_type


def enumerate_btree(folder):
    contagem_esperada = folder['_count'].value
    tree = folder['_tree']
    for contagem_real, (id, obj) in enumerate(tree.iteritems(), start=1):
        obj, meta_type = br(obj), type(obj).__name__
        yield id, obj, meta_type
    # verificação de consistência
    assert contagem_esperada == contagem_real


nao_identificados = defaultdict(list)


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


DUMP_FUNCTIONS = {
    'File': dump_file,
    'Image': dump_file,
    'Folder': partial(dump_folder, enum=enumerate_folder),
    'BTreeFolder2': partial(dump_folder, enum=enumerate_btree),

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


def dump_propriedades(docs):
    props_sapl = br(docs['props_sapl'])
    ids = [p['id'] for p in props_sapl['_properties']]
    props = {id: props_sapl[id] for id in ids}
    props = {id: p.decode('iso-8859-1') if isinstance(p, str) else p
             for id, p in props.items()}
    with open('sapl_documentos/propriedades.yaml', 'w') as f:
        f.write(yaml.safe_dump(props))


def dump_sapl(data_fs_path):
    app, close_db = get_app(data_fs_path)
    try:
        sapl = find_sapl(app)
        docs = br(sapl['sapl_documentos'])

        nao_identificados.clear()
        dump_folder(docs)
        dump_propriedades(docs)
        if nao_identificados:
            print('#' * 80)
            print('#' * 80)
            print(u'FORAM ENCONTRADOS ARQUIVOS DE FORMATO NÃO IDENTIFICADO!!!')
            print(u'REFAÇA A EXPORTAÇÃO\n')
            print(nao_identificados)
            print('#' * 80)
            print('#' * 80)
    finally:
        close_db()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        data_fs_path = sys.argv[1]
        dump_sapl(data_fs_path)
    else:
        print('Uso: python exporta_zope <caminho p Data.fs>')
