from django.db import models


class NivelInstrucao(models.Model):
    nivel_instrucao = models.CharField(max_length=50)
