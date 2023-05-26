import os
import base64
import re
from django.apps import apps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def extract_images(app_name, model_name, field_name, object_id=None):
    # Expressão regular para identificar a propriedade 'src' da imagem em base64
    image_data_re = re.compile(r'src=\"data:image/(?P<type>[a-z]+);base64,(?P<data>[^"]+)\"')

    try:
        Model = apps.get_model(app_name, model_name)
    except LookupError:
        print(f'O modelo "{model_name}" no aplicativo "{app_name}" não existe.')
        return

    # Obter todos os objetos ou um objeto específico
    if object_id is None:
        objects = Model.objects.all()
    else:
        objects = [Model.objects.get(id=object_id)]

    for obj in objects:
        new_text = getattr(obj, field_name)  # cópia do texto original
        for match in image_data_re.finditer(new_text):
            image_data = match.group('data')
            image_type = match.group('type')

            # Decodifica os dados da imagem em base64
            decoded_image = base64.b64decode(image_data)
            # Cria um objeto Django ContentFile para a imagem decodificada
            image_file = ContentFile(decoded_image)
            # Constroi um nome de arquivo
            filename = f'{obj.id}_{match.start()}.{image_type}'

            # Caminho personalizado para salvar o arquivo
            # Exemplo: sapl/public/dispositivo/123
            # todo: verificar se isso pode causar problemas com o armazenamento padrão
            folder_path = os.path.join('sapl', 'public', model_name.lower(), str(obj.id))

            # Salva o arquivo de imagem no armazenamento
            path = default_storage.save(os.path.join(folder_path, filename), image_file)

            # Substitui a propriedade 'src' da imagem pelos dados da imagem pela URL da imagem salva
            new_text = new_text.replace(match.group(), f'src="{default_storage.url(path)}"')
            print(f'Imagem salva em {path}')

        # Atualiza o campo com o novo texto
        print(f'Novo texto: {new_text}')
        setattr(obj, field_name, new_text)
        obj.save()

# Exemplo de uso:
# extract_images('compilacao', 'Dispositivo', 'texto')
# extract_images('compilacao', 'Dispositivo', 'texto', object_id=123)
