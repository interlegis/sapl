from datetime import date
from functools import wraps

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
            today = date.today()
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
