from sapl.crud.base import Crud, CrudListView
from sapl.crud.masterdetail import MasterDetailCrud

from .models import City, Country


class CountryCrud(Crud):
    model = Country
    help_topic = 'help_topic',

    class ListView(CrudListView):
        paginate_by = 10


class CityCrud(MasterDetailCrud):
    model = City
    help_topic = 'help_topic',
