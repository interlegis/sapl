from django.db import models


class LexmlRegistroProvedor(models.Model):
    id_provedor = models.IntegerField()                                         # id_provedor
    nome_provedor = models.CharField(max_length=255)                            # nom_provedor
    sigla_provedor = models.CharField(max_length=15)                            # sgl_provedor
    adm_email = models.CharField(max_length=50, blank=True, null=True)          # adm_email
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True)  # nom_responsavel
    tipo = models.CharField(max_length=50)                                      # tipo
    id_responsavel = models.IntegerField(blank=True, null=True)                 # id_responsavel
    xml_provedor = models.TextField(blank=True, null=True)                      # xml_provedor


class LexmlRegistroPublicador(models.Model):
    id_publicador = models.IntegerField()                                       # id_publicador
    nome_publicador = models.CharField(max_length=255)                          # nom_publicador
    adm_email = models.CharField(max_length=50, blank=True, null=True)          # adm_email
    sigla = models.CharField(max_length=255, blank=True, null=True)             # sigla
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True)  # nom_responsavel
    tipo = models.CharField(max_length=50)                                      # tipo
    id_responsavel = models.IntegerField()                                      # id_responsavel
