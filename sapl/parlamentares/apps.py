from django import apps
from django.db.models.signals import post_migrate
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist


def criar_grupo(permission):
    from django.contrib.auth.models import Group

    g = Group.objects.get_or_create(name='Votante')
    g[0].permissions.add(permission)


def criar_permissao(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    try:
        content_type = ContentType.objects.get(
            app_label='parlamentares',
            model='Votante')
    except ObjectDoesNotExist:
        content_type = ContentType.objects.create(
            app_label='parlamentares',
            model='Votante')

    p = Permission.objects.get_or_create(
        name='Can Vote', codename='can_vote', content_type=content_type)
    criar_grupo(p[0])


class AppConfig(apps.AppConfig):
    name = 'sapl.parlamentares'
    label = 'parlamentares'
    verbose_name = _('Parlamentares')

    def ready(self):
        post_migrate.connect(criar_permissao, sender=self)
