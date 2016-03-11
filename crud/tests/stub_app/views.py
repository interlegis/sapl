from crud.base import Crud, CrudListView

from .models import Country


class CountryCrud(Crud):
    model = Country
    help_path = 'help_path',

    class ListView(CrudListView):
        paginate_by = 10
