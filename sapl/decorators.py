from datetime import date
from functools import wraps


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
        try:
            string_displayed = decorated_method(self)
        except TypeError:
            string_displayed = ""

        if hasattr(self, 'data_inicio') and hasattr(self, 'data_fim'):
            today = date.today()
            e_atual = self.data_inicio <= today <= self.data_fim
            string_displayed = "{} {}".format(
                string_displayed, "(Atual)" if e_atual else "")
        else:
            print('{} {}'.format(
                "Instance does not have the attributes [{}, {}].".format(
                    'data_inicio',
                    'data_fim'
                ),
                "Decorator @{} has been disabled.".format(
                    vigencia_atual.__name__()
                    )
                )
            )

        return string_displayed

    return display_atual
