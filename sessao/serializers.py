"""
  This file is part of SAPL.
  Copyright (C) 2016 Interlegis
"""
from rest_framework import serializers

from .models import SessaoPlenaria


class SessaoPlenariaSerializer(serializers.ModelSerializer):

    class Meta:
        model = SessaoPlenaria
        fields = ('tipo', 'legislatura', 'sessao_legislativa')
