from functools import wraps

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


def vigencia_atual(decorated_method):
    """
    concatena a string ' (Atual)' caso a model instancia estiver
    em vigência na data atual do servidor

    Premissas:
        * A classe precisa conter os atributos 'data_inicio' e 'data_fim'.
        * 'data_inicio' e 'data_fim' precisam ser do tipo models.DateField
    """

    @wraps(decorated_method)
    def display_atual(self):
        string_displayed = decorated_method(self)

        if hasattr(self, 'data_inicio') and hasattr(self, 'data_fim'):
            today = timezone.now().today().date()
            e_atual = self.data_inicio <= today <= self.data_fim
            string_displayed = "{} {}".format(
                string_displayed, "(Atual)" if e_atual else "")
        else:
            instancia_sem_atributo = "{} [{}, {}].".format(
                'Instância não possui os atributos',
                'data_inicio',
                'data_fim')

            mensagem_decorator = "Decorator @{} foi desabilitado.".format(
                vigencia_atual.__name__()
            )
            print(_('{} {}'.format(
                _(instancia_sem_atributo),
                _(mensagem_decorator)
            )
            )
            )

        return string_displayed

    return display_atual


def receiver_multi_senders(signal, **kwargs):
    """
    A decorator for connecting receivers to signals. Used by passing in the
    signal (or list of signals) and keyword arguments to connect::

        @receiver(post_save, senders=MyModelsList)
        def signal_receiver(sender, **kwargs):
            ...

        @receiver([post_save, post_delete], senders=MyModelsList)
        def signals_receiver(sender, **kwargs):
            ...
    """

    def _decorator(func):
        senders = kwargs.get('senders', [])
        if isinstance(signal, (list, tuple)):
            if not senders:
                for s in signal:
                    s.connect(func, **kwargs)
            else:
                senders = kwargs.pop('senders')
                for sender in senders:
                    for s in signal:
                        s.connect(func, sender=sender, **kwargs)

        else:
            if not senders:
                signal.connect(func, **kwargs)
            else:
                senders = kwargs.pop('senders')
                for sender in senders:
                    signal.connect(func, sender=sender, **kwargs)

        return func

    return _decorator
