# -*- coding: utf-8 -*-

# IMPORTANTE:
# Esse script precisa rodar em python 2
# e depende apenas do descrito no arquivo requiments.txt

import os.path
from collections import defaultdict
from functools import partial

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


def dump_file(doc, path):
    name = doc['__name__']
    extension = EXTENSOES[doc['content_type']]
    fullname = os.path.join(path, name + extension)
    print(fullname)

    pdata = br(doc['data'])
    if isinstance(pdata, str):
        # Retrocedemos se pdata ja eh uma str (necessario em Images)
        pdata = doc

    with open(fullname, 'w') as arq:
        while pdata:
            arq.write(pdata['data'])
            pdata = br(pdata.get('next', None))
    return name


nao_identificados = defaultdict(list)


def enumerate_folder(folder):
    # folder vazio nao tem _objects
    for entry in folder.get('_objects', []):
        id, meta_type = entry['id'], entry['meta_type']
        obj = br(folder[id])
        yield id, obj, meta_type


def enumerate_btree(folder):
    tree = folder['_tree']
    for id, obj in tree.iteritems():
        obj, meta_type = br(obj), type(obj).__name__
        yield id, obj, meta_type


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
    [id] = [e['id'] for e in app['_objects']
            if e['id'].startswith('cm_')
            and e['meta_type'] == 'Folder']
    cm_zzz = br(app[id])
    sapl = br(cm_zzz['sapl'])
    return sapl


def dump_sapl(data_fs_path):
    app, close_db = get_app(data_fs_path)
    try:
        sapl = find_sapl(app)
        docs = br(sapl['sapl_documentos'])

        nao_identificados.clear()
        dump_folder(docs)
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
