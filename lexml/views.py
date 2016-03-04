"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from django.utils.translation import ugettext_lazy as _

from crud import Crud

from .models import LexmlProvedor, LexmlPublicador

lexml_provedor_crud = Crud(LexmlProvedor, 'lexml_provedor')
lexml_publicador_crud = Crud(LexmlPublicador, 'lexml_publicador')
