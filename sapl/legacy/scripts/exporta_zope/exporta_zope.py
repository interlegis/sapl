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
from os.path import exists

import git
import magic
import yaml
import ZODB.DB
import ZODB.FileStorage
from unipath import Path
from ZODB.broken import Broken
from ZODB.POSException import POSKeyError

from variaveis_comuns import DIR_DADOS_MIGRACAO, TAG_ZOPE

EXTENSOES = {
    # docs
    'application/msword': '.doc',
    'application/pdf': '.pdf',
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',  # noqa
    'application/vnd.oasis.opendocument.text-template': '.ott',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',  # noqa
    'application/vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',  # noqa
    'application/vnd.oasis.opendocument.graphics': '.odg',

    # incertos... associamos a extensão mais provável
    'application/vnd.ms-office': '.doc',
    'text/x-c++': '.cpp',

    # outros
    'application/xml': '.xml',
    'text/xml': '.xml',
    'application/zip': '.zip',
    'application/x-rar': '.rar',
    'application/x-dosexec': '.exe',
    'message/rfc822': '.mht',
    'text/richtext': '.rtx',
    'application/gzip': '.gz',
    'image/vnd.dwg': '*.dwg',

    # media
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
    'image/x-ms-bmp': '.bmp',
    'video/x-ms-asf': '.asf',
    'audio/mpeg': '.mp3',
    'video/x-flv': '.flv',
    'video/quicktime': '.mov',

    # sem extensao
    'application/octet-stream': '',  # binário
    'inode/x-empty': '',  # vazio
    'application/x-empty': '',  # vazio
    'text/x-unknown-content-type': '',  # desconhecido
    'application/CDFV2-unknown': '',  # desconhecido
}


def br(obj):
    if isinstance(obj, Broken):
        return obj.__Broken_state__
    else:
        return obj


def guess_extension(fullname, buffer):
    # um corte de apenas 1024 impediu a detecção correta de .docx
    mime = magic.from_buffer(buffer, mime=True)
    extensao = EXTENSOES.get(mime)
    if extensao is not None:
        return extensao
    else:
        possibilidades = '\n'.join(
            ["    '{}': '{}',".format(mime, ext)
             for ext in mimetypes.guess_all_extensions(mime)])
        print('''Extensão não conhecida para o arquivo: {}
            e mimetype: {}
            Algumas possibilidades são:
            {}
            Atualize o código do dicionário EXTENSOES!
            '''.format(fullname, mime, possibilidades)
              )
        return '.DESCONHECIDO.{}'.format(mime.replace('/', '__'))


CONTEUDO_ARQUIVO_CORROMPIDO = 'ARQUIVO CORROMPIDO'


def get_conteudo_file(doc):
    # A partir daqui usamos dict.pop('...') nos __Broken_state__
    # para contornar um "vazamento" de memória que ocorre
    # ao percorrer a árvore de objetos
    #
    # Imaginamos que, internamente, o ZODB está guardando referências
    # para os objetos Broken criados e não conseguimos identificar como.
    #
    # Essa medida descarta quase todos os dados retornados
    # e só funciona na primeira passagem
    try:
        pdata = br(doc.pop('data'))
        if isinstance(pdata, str):
            # Retrocedemos se pdata ja eh uma str (necessario em Images)
            doc['data'] = pdata
            pdata = doc

        output = cStringIO.StringIO()
        while pdata:
            output.write(pdata.pop('data'))
            pdata = br(pdata.pop('next', None))

        return output.getvalue()
    except POSKeyError:
        return CONTEUDO_ARQUIVO_CORROMPIDO


def dump_file(doc, path, salvar, get_conteudo=get_conteudo_file):
    name = doc['__name__']
    fullname = os.path.join(path, name)
    conteudo = get_conteudo(doc)
    if conteudo == CONTEUDO_ARQUIVO_CORROMPIDO:
        fullname = fullname + '_CORROMPIDO'
        print('ATENÇÃO: arquivo corrompido: {}'.format(fullname))
    if conteudo:
        # pula arquivos vazios
        salvar(fullname, conteudo)
    return name


def get_conteudo_dtml_method(doc):
    return doc['raw']


def print_msg_poskeyerror(id):
    print('#' * 80)
    print('#' * 80)
    print('ATENÇÃO: DIRETÓRIO corrompido: {}'.format(id))
    print('#' * 80)
    print('#' * 80)


def enumerate_by_key_list(folder, key_list, type_key):
    for entry in folder.get(key_list, []):
        id, meta_type = entry['id'], entry[type_key]
        try:
            obj = folder.get(id, None)
        except POSKeyError:
            print_msg_poskeyerror(id)
        else:
            yield id, obj, meta_type


enumerate_folder = partial(enumerate_by_key_list,
                           key_list='_objects', type_key='meta_type')

enumerate_properties = partial(enumerate_by_key_list,
                               key_list='_properties', type_key='type')


def enumerate_btree(folder):
    contagem_esperada = folder['_count'].value
    tree = folder['_tree']
    contagem_real = 0  # para o caso em que não haja itens
    try:
        for contagem_real, (id, obj) in enumerate(tree.iteritems(), start=1):
            meta_type = type(obj).__name__
            yield id, obj, meta_type
    except POSKeyError:
        print_msg_poskeyerror(folder['id'])
    # verificação de consistência
    if contagem_esperada != contagem_real:
        print('ATENÇÃO: contagens diferentes na btree: '
              '{} esperada: {} real: {}'.format(folder['title'],
                                                contagem_esperada,
                                                contagem_real))


nao_identificados = defaultdict(list)


@contextmanager
def logando_nao_identificados():
    nao_identificados.clear()
    yield
    if nao_identificados:
        print('#' * 80)
        print('#' * 80)
        print('FORAM ENCONTRADOS ARQUIVOS DE FORMATO NÃO IDENTIFICADO!!!')
        print('REFAÇA A EXPORTAÇÃO\n')
        print(nao_identificados)
        print('#' * 80)
        print('#' * 80)


def dump_folder(folder, path, salvar, mtimes, enum=enumerate_folder):
    name = folder['id']
    path = os.path.join(path, name)
    if not exists(path):
        os.makedirs(path)
    for id, obj, meta_type in enum(folder):
        # pula pastas *_old (presentes em várias bases)
        if id.endswith('_old') and meta_type in ['Folder', 'BTreeFolder2']:
            continue
        dump = DUMP_FUNCTIONS.get(meta_type, '?')
        if dump == '?':
            nao_identificados[meta_type].append(path + '/' + id)
        elif dump:
            if isinstance(dump, partial) and dump.func == dump_folder:
                try:
                    dump(br(obj), path, salvar, mtimes)
                except POSKeyError as e:
                    print_msg_poskeyerror(id)
                    continue
            else:
                # se o objeto for mais recente que o da última exportação
                mtime = obj._p_mtime
                fullname = os.path.join(path, id)
                if mtime > mtimes.get(fullname, 0):
                    id_interno = dump(br(obj), path, salvar)
                    assert id == id_interno
                    mtimes[fullname] = mtime
    return name


def decode_iso8859(obj):
    return obj.decode('iso8859-1') if isinstance(obj, str) else obj


def read_sde(element):

    def read_properties():
        for id, obj, meta_type in enumerate_properties(element):
            yield id, decode_iso8859(br(obj))

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
                       'dados': read_sde(br(obj))}

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
    'DTML Method': partial(dump_file,
                           get_conteudo=get_conteudo_dtml_method),
    'DTMLMethod': partial(dump_file,
                          get_conteudo=get_conteudo_dtml_method),
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
    ids_meta_types = [(obj['id'], obj['meta_type']) for obj in app['_objects']]
    # estar ordenado é muito importante para que a busca dê prioridade
    # a um id "cm_zzz" antes do id "sapl"
    for id, meta_type in sorted(ids_meta_types):
        if id.startswith('cm_') and meta_type == 'Folder':
            cm_zzz = br(app[id])
            return find_sapl(cm_zzz)
        elif id == 'sapl' and meta_type in ['SAPL', 'Folder']:
            sapl = br(app['sapl'])
            return sapl


def detectar_encoding(fonte):
    desc = magic.from_buffer(fonte)
    for termo, enc in [('ISO-8859', 'latin1'), ('UTF-8', 'utf-8')]:
        if termo in desc:
            return enc
    return None


def autodecode(fonte):
    if isinstance(fonte, str):
        enc = detectar_encoding(fonte)
        return fonte.decode(enc) if enc else fonte
    else:
        return fonte


def dump_propriedades(docs, path, salvar):
    props_sapl = br(docs['props_sapl'])
    ids = [p['id'] for p in props_sapl['_properties']]
    props = {id: props_sapl[id] for id in ids}
    props = {id: autodecode(p) for id, p in props.items()}
    save_as_yaml(path, 'sapl_documentos/propriedades.yaml', props, salvar)


def dump_usuarios(sapl, path, salvar):
    users = br(br(sapl['acl_users'])['data'])
    users = {autodecode(k): br(v) for k, v in users['data'].items()}
    for dados in users.values():
        dados['name'] = autodecode(dados['name'])
    save_as_yaml(path, 'usuarios.yaml', users, salvar)


def _dump_sapl(data_fs_path, documentos_fs_path, destino, salvar, mtimes):
    assert exists(data_fs_path)
    assert exists(documentos_fs_path)
    # precisamos trabalhar com strings e não Path's para as comparações de mtimes
    data_fs_path, documentos_fs_path, destino = map(str, (
        data_fs_path, documentos_fs_path, destino))

    app, close_db = get_app(data_fs_path)
    try:
        sapl = find_sapl(app)
        # extrai usuários com suas senhas e perfis
        dump_usuarios(sapl, destino, salvar)

        # extrai folhas XSLT (primeira tentativa)
        if 'XSLT' in sapl:
            dump_folder(br(sapl['XSLT']), destino, salvar, mtimes)

    finally:
        close_db()

    app, close_db = get_app(documentos_fs_path)

    try:
        sapl = find_sapl(app)
        if sapl == {'id': 'sapl'}:
            # em algumas instalações sapl_documentos está direto na raiz
            docs = br(app['sapl_documentos'])
        else:
            # caso mais comum
            docs = br(sapl['sapl_documentos'])

            # extrai folhas XSLT (segunda tentativa)
            if 'XSLT' in sapl:
                dump_folder(br(sapl['XSLT']), destino, salvar, mtimes)

        # extrai documentos
        with logando_nao_identificados():
            dump_folder(docs, destino, salvar, mtimes)
            dump_propriedades(docs, destino, salvar)
    finally:
        close_db()


def repo_execute(repo, cmd, *args):
    return repo.git.execute(cmd.split() + list(args))


def ajusta_extensao(fullname, conteudo):
    base, extensao = os.path.splitext(fullname)
    if extensao not in ['.xsl', '.xslt', '.yaml', '.css']:
        extensao = guess_extension(fullname, conteudo)
    return base + extensao, extensao


def build_salvar(repo):

    def salvar(fullname, conteudo):
        fullname, extensao = ajusta_extensao(fullname, conteudo)

        # ajusta caminhos XSLT p conteúdos relacionados ao SDE
        if extensao in ['.xsl', '.xslt', '.xml']:
            conteudo = conteudo.replace('"XSLT/HTML', '"/XSLT/HTML')

        if exists(fullname):
            # destrava arquivo pré-existente (o conteúdo mudou)
            repo_execute(repo, 'git annex unlock', fullname)
        with open(fullname, 'w') as arq:
            arq.write(conteudo)
        print(fullname)

    return salvar


def dump_sapl(sigla):
    sigla = sigla[-3:]  # ignora prefixo (por ex. 'sapl_cm_')
    data_fs_path, documentos_fs_path = [
        DIR_DADOS_MIGRACAO.child(
            'datafs', '{}_cm_{}.fs'.format(prefixo, sigla))
        for prefixo in ('Data', 'DocumentosSapl')]

    assert exists(data_fs_path), 'Origem não existe: {}'.format(data_fs_path)
    if not exists(documentos_fs_path):
        documentos_fs_path = data_fs_path

    nome_banco_legado = 'sapl_cm_{}'.format(sigla)
    destino = DIR_DADOS_MIGRACAO.child('repos', nome_banco_legado)
    destino.mkdir(parents=True)
    repo = git.Repo.init(destino)
    if TAG_ZOPE in repo.tags:
        print('{}: A exportação de documentos já está feita -- abortando'.format(sigla))
        return

    repo_execute(repo, 'git annex init')
    repo_execute(repo, 'git config annex.thin true')

    salvar = build_salvar(repo)
    try:
        finalizado = False
        arq_mtimes = Path(repo.working_dir, 'mtimes.yaml')
        mtimes = yaml.load(
            arq_mtimes.read_file()) if arq_mtimes.exists() else {}
        _dump_sapl(data_fs_path, documentos_fs_path, destino, salvar, mtimes)
        finalizado = True
    finally:
        # grava mundaças
        repo_execute(repo, 'git annex add sapl_documentos')
        arq_mtimes.write_file(yaml.safe_dump(mtimes, allow_unicode=True))
        repo.git.add(A=True)
        # atualiza repo
        if 'master' not in repo.heads or repo.index.diff('HEAD'):
            # se de fato existe mudança
            status = 'completa' if finalizado else 'parcial'
            repo.index.commit(u'Exportação do zope {}'.format(status))
        if finalizado:
            repo.git.execute('git tag -f'.split() + [TAG_ZOPE])


if __name__ == "__main__":
    if len(sys.argv) == 2:
        sigla = sys.argv[1]
        dump_sapl(sigla)
    else:
        print('Uso: python exporta_zope <sigla>')
