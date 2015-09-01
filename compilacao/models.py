from django.db import models
from django.utils.translation import ugettext_lazy as _
from sapl.utils import YES_NO_CHOICES, make_choices


class TipoNota(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    modelo = models.TextField(
        blank=True, null=True, verbose_name=_('Modelo'))

    class Meta:
        verbose_name = _('Tipo de Nota')
        verbose_name_plural = _('Tipos de Nota')

    def __str__(self):
        return self.sigla
    
    
class TipoVide(models.Model):
    sigla = models.CharField(max_length=10, verbose_name=_('Sigla'))
    nome = models.CharField(max_length=50, verbose_name=_('Nome'))
    
    class Meta:
        verbose_name = _('Tipo de Vide')
        verbose_name_plural = _('Tipos de Vide')

    def __str__(self):
        return self.sigla
    
    
class TipoDispositivo(models.Model):
    FORMATO_NUMERACAO = [
        ('1', _('Numérico')), 
        ('I', _('Romano Maiúsculo')), 
        ('i', _('Romano Minúsculo')), 
        ('A', _('Alfabético Maiúsculo')), 
        ('a', _('Alfabético Minúsculo')), 
        ('*', _('Tópico sem contagem')),    
        ('N', _('Sem renderização de Contagem')),     
    ]
    
    nome = models.CharField(
        max_length=50, unique = True, verbose_name=_('Nome'))
    class_css = models.CharField(
        max_length=20, verbose_name=_('Classe CSS'))
    rotulo_prefixo_html = models.CharField(
        max_length=100, verbose_name=_('Prefixo html do rótulo'))
    rotulo_prefixo_texto = models.CharField(
        max_length=30,
        verbose_name=_('Prefixo de construção do rótulo'))
    rotulo_ordinal = models.IntegerField(
        verbose_name=_('Tipo de Número do Rótulo')) 
    rotulo_separadores_variacao = models.CharField(
        max_length=5, verbose_name=_('Separadores das Variações'))    
    rotulo_sufixo_texto = models.CharField(
        max_length=30,
        verbose_name=_('Sufixo de construção do rótulo'))
    rotulo_sufixo_html = models.CharField(
        max_length=100, verbose_name=_('Sufixo html do rótulo'))
    texto_prefixo_html = models.CharField(
        max_length=100, verbose_name=_('Prefixo html do texto'))
    texto_sufixo_html = models.CharField(
        max_length=100, verbose_name=_('Sufixo html do texto'))
    nota_automatica_prefixo_html = models.CharField(
        max_length=100, verbose_name=_('Prefixo html da Nota Automática'))
    nota_automatica_sufixo_html = models.CharField(
        max_length=100, verbose_name=_('Sufixo html da Nota Automática'))
    contagem_continua = models.BooleanField(
        choices=YES_NO_CHOICES, verbose_name=_('Contagem contínua'))
    formato_variacao0 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO,
        verbose_name=_('Formato da Numeração'))
    formato_variacao1 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO,
        verbose_name=_('Formato da Variação 1'))
    formato_variacao2 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO,
        verbose_name=_('Formato da Variação 2'))
    formato_variacao3 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO,
        verbose_name=_('Formato da Variação 3'))
    formato_variacao4 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO,
        verbose_name=_('Formato da Variação 4'))
    formato_variacao5 = models.CharField(
        max_length=1,
        choices=FORMATO_NUMERACAO,
        verbose_name=_('Formato da Variação 5'))
    
    
    
    class Meta:
        verbose_name = _('Tipo de Dispositivo')
        verbose_name_plural = _('Tipos de Dispositivo')
        
    def __str__(self):
        return self.sigla
