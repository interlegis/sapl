from exporta_zope import (br, dump_folder, dump_propriedades, dump_usuarios,
                          get_app, logando_nao_identificados)


def dump_sapl30():
    """Extrai dados do zope de um sapl 3.0, que, ao que tudo indica:
        * não possui a pasta XSLT
        * usa um mountpoint separado para os documentos
    """
    try:
        destino = '../../../../media'
        data_fs_path = destino + '/Data.fs'
        docs_path = destino + '/DocumentosSapl.fs'
        app, close_db = get_app(data_fs_path)
        sapl = br(app['sapl'])
        dump_usuarios(sapl, destino)
    finally:
        close_db()

    try:
        app, close_db = get_app(docs_path)
        docs = br(app['sapl_documentos'])
        with logando_nao_identificados():
            dump_folder(docs, destino)
            dump_propriedades(docs, destino)
    finally:
        close_db()
