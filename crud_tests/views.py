from crud import Crud, CrudListMixin

from .models import Country


class CountryCrudListMixin(CrudListMixin):
    paginate_by = 10


country_crud = Crud(
    Country,
    'help_path',
    list_mixin=CountryCrudListMixin)
