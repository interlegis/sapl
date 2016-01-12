from rest_framework import serializers
from .models import SessaoPlenaria

class SessaoPlenariaSerializer(serializers.ModelSerializer):

	class Meta:
		model = SessaoPlenaria
		fields = ('tipo', 'legislatura', 'sessao_legislativa')