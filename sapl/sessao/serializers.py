from rest_framework import serializers

from .models import SessaoPlenaria


class SessaoPlenariaSerializer(serializers.Serializer):

    class Meta:
        model = SessaoPlenaria
        fields = ('tipo',
                  'sessao_legislativa',
                  'legislatura',
                  'data_inicio',
                  'hora_inicio',
                  'hora_fim',
                  'url_video',
                  'iniciada',
                  'finalizada'
                  )
