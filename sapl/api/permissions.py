from rest_framework.permissions import DjangoModelPermissions


class DjangoModelPermissions(DjangoModelPermissions):

    perms_map = {
        'GET': ['%(app_label)s.list_%(model_name)s',
                '%(app_label)s.detail_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.list_%(model_name)s',
                    '%(app_label)s.detail_%(model_name)s'],
        'HEAD': ['%(app_label)s.list_%(model_name)s',
                 '%(app_label)s.detail_%(model_name)s'],
        'POST': ['%(app_label)s.list_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],

    }
