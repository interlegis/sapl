from django.core.exceptions import ValidationError
from django.forms import ModelForm
from sapl.settings import PROJECT_DIR
from django.utils.translation import ugettext_lazy as _

from io import StringIO
from lxml import etree
import os
import re
import xml.dom.minidom as dom

from .models import LexmlProvedor


class LexmlProvedorForm(ModelForm):
    class Meta:
        model = LexmlProvedor
        fields = [
            "id_provedor",
            "nome",
            "id_responsavel",
            "nome_responsavel",
            "email_responsavel",
            "xml"
        ]

    def clean(self):
        cd = super().clean()

        if not self.is_valid():
            return cd

        if cd["xml"]:
            xml = re.sub("\n|\t", "", cd["xml"].strip())

            validar_xml(xml)
            validar_schema(xml)

        return cd


def validar_xml(xml):
    xml = StringIO(xml)
    try:
        dom.parse(xml)
    except Exception as e:
        raise ValidationError(_(F"XML mal formatado. Error: {e}"))

def validar_schema(xml):
    xml_schema = open(os.path.join(PROJECT_DIR, 'sapl/templates/lexml/schema.xsd'), 'rb').read()
    schema_root = etree.XML(xml_schema)
    schema = etree.XMLSchema(schema_root)
    parser = etree.XMLParser(schema=schema)
    try:
        root = etree.fromstring(xml.encode(), parser)
    except Exception as e:
        raise ValidationError(_(F"XML mal formatado. Error: {e}"))
