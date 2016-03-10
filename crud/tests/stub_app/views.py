from crud.base import Crud, ListMixin

from .models import Country


class CountryListMixin(ListMixin):
    paginate_by = 10


country_crud = Crud(
    Country,
    'help_path',
    list_mixin=CountryListMixin)
