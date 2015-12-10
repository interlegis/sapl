from django.db import models


class Painel(models.Model):
    PAINEL_TYPES = (
        ('C', 'Completo'),
        ('P', 'Parlamentares'),
        ('V', 'Votação'),
        ('M', 'Mensagem'),
    )

    aberto = models.BooleanField(verbose_name='Abrir painel', default=False)
    data_painel = models.DateField(verbose_name='Data painel')
    mostrar = models.CharField(max_length=1,
                               choices=PAINEL_TYPES, default='C')

    def __str__(self):
        return str(self.aberto) + ":" + self.data_painel.strftime("%d/%m/%Y")


class Cronometro(models.Model):
    CRONOMETRO_TYPES = (
        ('A', 'Aparte'),
        ('D', 'Discurso'),
        ('O', 'Ordem do dia')
    )

    CRONOMETRO_STATUS = (
        ('I', 'Start'),
        ('R', 'Reset'),
        ('S', 'Stop'),
    )

    status = models.CharField(
        max_length=1,
        verbose_name='Status do cronômetro',
        choices=CRONOMETRO_STATUS,
        default='S')
    data_cronometro = models.DateField(verbose_name='Data do cronômetro')
    tipo = models.CharField(
        max_length=1, choices=CRONOMETRO_TYPES, verbose_name='Tipo Cronômetro')
