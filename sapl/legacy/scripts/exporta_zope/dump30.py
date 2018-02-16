from exporta_zope import (br, dump_folder, dump_propriedades, dump_usuarios,
                          get_app, logando_nao_identificados)


def dump_sapl30():
    destino = '../../../../media'
    data_fs_path = destino + '/Data.fs'
    docs_path = destino + '/DocumentosSapl.fs'
    app, close_db = get_app(data_fs_path)
    sapl = br(app['sapl'])
    dump_usuarios(sapl, destino)
    close_db()

    app, close_db = get_app(docs_path)
    docs = br(app['sapl_documentos'])
    with logando_nao_identificados():
        dump_folder(docs, destino)
        dump_propriedades(docs, destino)
