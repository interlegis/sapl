from django import forms
from django.utils.translation import ugettext_lazy as _


class UpLoadImportFileForm(forms.Form):
    import_file = forms.FileField(
        required=True,
        label=_('Arquivo formato ODF para Importanção'))
