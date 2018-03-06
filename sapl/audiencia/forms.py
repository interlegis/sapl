from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from sapl.audiencia.models import AudienciaPublica, TipoAudienciaPublica
from sapl.materia.models import MateriaLegislativa

class AudienciaForm(forms.ModelForm):

    materia = forms.ModelChoiceField(required=False,
                                     queryset=MateriaLegislativa.objects.all().select_related(
                                         "tipo").order_by('tipo', '-ano', 'numero'))

    tipo = forms.ModelChoiceField(required=True,
                                  queryset=TipoAudienciaPublica.objects.all().order_by('nome'))


    class Meta:
        model = AudienciaPublica
        fields = '__all__'


    def __init__(self, **kwargs):
        super(AudienciaForm, self).__init__(**kwargs)

        tipos = []

        if not self.fields['tipo'].queryset:
            tipos.append(TipoAudienciaPublica.objects.create(nome='Audiência Pública', tipo='A'))
            tipos.append(TipoAudienciaPublica.objects.create(nome='Plebiscito', tipo='P'))
            tipos.append(TipoAudienciaPublica.objects.create(nome='Referendo', tipo='R'))
            tipos.append(TipoAudienciaPublica.objects.create(nome='Iniciativa Popular', tipo='I'))

            for t in tipos:
                t.save()


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