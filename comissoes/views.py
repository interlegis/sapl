from django.utils.translation import ugettext as _

from .forms import ComissaoForm
from sapl.crud import Crud


comissao_crud = Crud(ComissaoForm, _('Nova Comissão'))
