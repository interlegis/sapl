from .forms import ComissaoForm
from sapl.crud import build_crud


comissao_crud = build_crud(ComissaoForm)
