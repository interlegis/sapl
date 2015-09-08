from django.db import models


class Cronometro(models.Model):
    CRONOMETRO_TYPES = (
        ('A', 'Aparte'),
        ('D', 'Discurso'),
        ('O', 'Ordem do dia')
    )

    start = models.PositiveIntegerField(verbose_name='Iniciar cronômetro')
    reset = models.PositiveIntegerField(verbose_name='Reiniciar cronômetro')
    stop = models.PositiveIntegerField(verbose_name='Parar cronômetro')
    data = models.DateField(verbose_name='Data cronômetro')
    tipo = models.CharField(
        max_length=1, choices=CRONOMETRO_TYPES, verbose_name='Tipo Cronômetro')


class Painel(models.Model):
    PAINEL_TYPES = (
        ('C', 'Completo'),
        ('P', 'Parlamentares'),
        ('V', 'Votação'),
        ('M', 'Mensagem'),
    )

    abrir = models.PositiveIntegerField(verbose_name='Abrir painel', default=0)
    fechar = models.PositiveIntegerField(
        verbose_name='Fechar painel', default=1)
    data_painel = models.DateField(verbose_name='Data painel')
    mostrar = models.CharField(max_length=1,
                               choices=PAINEL_TYPES,
                               default='C')
