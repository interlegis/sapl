from django.db import models


class LexmlRegistroProvedor(models.Model):
    id_provedor = models.IntegerField()
    nom_provedor = models.CharField(max_length=255)
    sgl_provedor = models.CharField(max_length=15)
    adm_email = models.CharField(max_length=50, blank=True, null=True)
    nom_responsavel = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50)
    id_responsavel = models.IntegerField(blank=True, null=True)
    xml_provedor = models.TextField(blank=True, null=True)


class LexmlRegistroPublicador(models.Model):
    id_publicador = models.IntegerField()
    nom_publicador = models.CharField(max_length=255)
    adm_email = models.CharField(max_length=50, blank=True, null=True)
    sigla = models.CharField(max_length=255, blank=True, null=True)
    nom_responsavel = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=50)
    id_responsavel = models.IntegerField()
