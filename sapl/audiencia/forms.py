from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica

class AudienciaForm(forms.ModelForm):

    class Meta:
        model = AudienciaPublica
        fields = '__all__'

    def clean(self):
        super(AudienciaForm, self).clean()
        if self.cleaned_data['hora_inicio'] and self.cleaned_data['hora_fim']:
            if (self.cleaned_data['hora_fim'] <
                self.cleaned_data['hora_inicio']):
                    msg = _('A hora de fim não pode ser anterior a hora de ínicio')
                    raise ValidationError(msg)

        return self.cleaned_data

    @transaction.atomic()
    def save(self, commit=True):
        audiencia = super(AudienciaForm, self).save(commit)
        return audiencia