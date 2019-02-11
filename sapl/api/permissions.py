from rest_framework.permissions import DjangoModelPermissions
from sapl.rules.map_rules import rules_patterns_public


class SaplModelPermissions(DjangoModelPermissions):

    perms_map = {
        'GET': ['%(app_label)s.list_%(model_name)s',
                '%(app_label)s.detail_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.list_%(model_name)s',
                    '%(app_label)s.detail_%(model_name)s'],
        'HEAD': ['%(app_label)s.list_%(model_name)s',
                 '%(app_label)s.detail_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],

    }

    def has_permission(self, request, view):
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
        else:
            queryset = getattr(view, 'queryset', None)

        assert queryset is not None, (
            'Cannot apply DjangoModelPermissions on a view that '
            'does not set `.queryset` or have a `.get_queryset()` method.'
        )

        perms = self.get_required_permissions(request.method, queryset.model)

        key = '{}:{}'.format(
            queryset.model._meta.app_label,
            queryset.model._meta.model_name)

        if key in rules_patterns_public:
            perms = set(perms)
            perms_publicas = rules_patterns_public[key]

            private_perms = perms - perms_publicas
            if not private_perms:
                return True

        return (
            request.user and
            (request.user.is_authenticated() or not self.authenticated_users_only) and
            request.user.has_perms(perms)
        )
