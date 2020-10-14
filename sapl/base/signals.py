from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.db.utils import DEFAULT_DB_ALIAS
import django.dispatch

from django.utils.translation import ugettext_lazy as _
from sapl.base.models import Autor, TipoAutor
from sapl.utils import models_with_gr_for_model


tramitacao_signal = django.dispatch.Signal(providing_args=['post', 'request'])


def cria_models_tipo_autor(app_config=None, verbosity=2, interactive=True,
                           using=DEFAULT_DB_ALIAS, **kwargs):

    models = models_with_gr_for_model(Autor)

    print("\n\033[93m\033[1m{}\033[0m".format(
        _('Atualizando registros TipoAutor do SAPL:')))
    for model in models:
        content_type = ContentType.objects.get_for_model(model)
        tipo_autor = TipoAutor.objects.filter(
            content_type=content_type.id).exists()

        if tipo_autor:
            msg1 = "Carga de {} não efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " Já Existe um {} {} relacionado...".format(
                TipoAutor._meta.verbose_name,
                model._meta.verbose_name)
            msg = "  {}{}".format(msg1, msg2)
        else:
            novo_autor = TipoAutor()
            novo_autor.content_type_id = content_type.id
            novo_autor.descricao = model._meta.verbose_name
            novo_autor.save()
            msg1 = "Carga de {} efetuada.".format(
                TipoAutor._meta.verbose_name)
            msg2 = " {} {} criado...".format(
                TipoAutor._meta.verbose_name, content_type.model)
            msg = "  {}{}".format(msg1, msg2)
        print(msg)
    # Disconecta função para evitar a chamada repetidas vezes.
    post_migrate.disconnect(receiver=cria_models_tipo_autor)


post_migrate.connect(receiver=cria_models_tipo_autor)
