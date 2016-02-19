from crud import Crud, CrudListMixin

from .models import Country


class CountryCrudListMixin(CrudListMixin):
    paginate_by = 10


country_crud = Crud(
    Country, 'help_path', [
        ['Basic Data',
         [('name', 9), ('continent', 3)],
         [('population', 6), ('is_cold', 6)]
         ],
        ['More Details', [('description', 12)]],
    ],
    crud_list_mixin=CountryCrudListMixin)
