from django.core.validators import RegexValidator
from django.db import models


class ConfiguracaoImpressao(models.Model):
    # Campo para ser o identificador único da configuração de impressão
    identificador = models.CharField(
        max_length=100,
        unique=True,
        help_text="Identificador único da configuração",
        validators=[
            RegexValidator(
                r'^[A-Z0-9_-]+$',
                'Digite apenas letras maiúsculas, números, underline (_) ou hífen (-).'
            )
        ]
    )

    # Campos para a configuração da página de impressão
    nome = models.CharField(max_length=100, help_text="Nome da configuração de impressão")
    # Campo de descrição para que o usuário possa identificar a configuração
    descricao = models.TextField(blank=True, help_text="Descrição da configuração de impressão")
    largura_pagina = models.DecimalField(max_digits=6, decimal_places=2, default=800,
                                         help_text="Largura da página em pixels")
    altura_pagina = models.DecimalField(max_digits=6, decimal_places=2, default=1200,
                                        help_text="Altura da página em pixels")
    margem_superior = models.DecimalField(max_digits=6, decimal_places=2, default=20,
                                          help_text="Margem superior da página em pixels")
    margem_inferior = models.DecimalField(max_digits=6, decimal_places=2, default=20,
                                          help_text="Margem inferior da página em pixels")
    margem_esquerda = models.DecimalField(max_digits=6, decimal_places=2, default=20,
                                          help_text="Margem esquerda da página em pixels")
    margem_direita = models.DecimalField(max_digits=6, decimal_places=2, default=20,
                                         help_text="Margem direita da página em pixels")
    cor_fundo = models.CharField(max_length=7, default="#FFFFFF",
                                 help_text="Cor de fundo da página em formato hexadecimal")
    tamanho_fonte = models.PositiveIntegerField(default=12,
                                                help_text="Tamanho padrão da fonte em pixels")
    cor_fonte = models.CharField(max_length=7, default="#000000",
                                 help_text="Cor padrão da fonte em formato hexadecimal")
    fonte = models.CharField(max_length=100, default="Arial",
                             help_text="Família da fonte utilizada")
    espacamento_linhas = models.DecimalField(max_digits=6, decimal_places=2, default=1,
                                             help_text="Espaçamento entre linhas em pixels")

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Configuração de Impressão"
        verbose_name_plural = "Configurações de Impressão"
        ordering = ['identificador', 'nome']
