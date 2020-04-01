import logging

from django import forms
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from sapl.sdr.models import DeliberacaoRemota


class DeliberacaoRemotaCreateForm(ModelForm):
    logger = logging.getLogger(__name__)

    class Meta:
        model = DeliberacaoRemota
        exclude = []

        widgets = {
            'created_by': forms.HiddenInput(),
            'descricao': forms.Textarea(attrs={'id': 'texto-rico'})
        }

    def clean(self):
        cleaned_data = super().clean()
        import ipdb; ipdb.set_trace()
        if not self.is_valid():
            return self.cleaned_data

        return cleaned_data

# class DeliberacaoRemotaForm(ModelForm):
#
#     logger = logging.getLogger(__name__)
#
#     class Meta:
#         model = DeliberacaoRemota
#         fields = ['chat_id', 'descricao']
#     class AutoriaNormaForm(ModelForm):
#
#         tipo_autor = ModelChoiceField(label=_('Tipo Autor'),
#                                       required=False,
#                                       queryset=TipoAutor.objects.all(),
#                                       empty_label=_('Selecione'), )
#
#         data_relativa = forms.DateField(
#             widget=forms.HiddenInput(), required=False)
#
#         logger = logging.getLogger(__name__)
#
#         def __init__(self, *args, **kwargs):
#             super(AutoriaNormaForm, self).__init__(*args, **kwargs)
#
#             row1 = to_row([('tipo_autor', 4),
#                            ('autor', 4),
#                            ('primeiro_autor', 4)])
#
#             self.helper = SaplFormHelper()
#             self.helper.layout = Layout(
#                 Fieldset(_('Autoria'),
#                          row1, 'data_relativa', form_actions(label='Salvar')))
#
#             if not kwargs['instance']:
#                 self.fields['autor'].choices = []
#
#         class Meta:
#             model = AutoriaNorma
#             fields = ['tipo_autor', 'autor', 'primeiro_autor', 'data_relativa']
#
#         def clean(self):
#             cd = super(AutoriaNormaForm, self).clean()
#
#             if not self.is_valid():
#                 return self.cleaned_data
#
#             autorias = AutoriaNorma.objects.filter(
#                 norma=self.instance.norma, autor=cd['autor'])
#             pk = self.instance.pk
#
#             if ((not pk and autorias.exists()) or
#                     (pk and autorias.exclude(pk=pk).exists())):
#                 self.logger.error(
#                     "Autor ({}) já foi cadastrado.".format(cd['autor']))
#                 raise ValidationError(_('Esse Autor já foi cadastrado.'))
#
#             return cd