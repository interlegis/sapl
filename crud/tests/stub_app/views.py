from crud.base import Crud, CrudListView
from crud.masterdetail import MasterDetailCrud

from .models import City, Country


class CountryCrud(Crud):
    model = Country
    help_path = 'help_path',

    class ListView(CrudListView):
        paginate_by = 10


class CityCrud(MasterDetailCrud):
    model = City
    help_path = 'help_path',
