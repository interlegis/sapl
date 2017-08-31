# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

def gera_partidos_tse(apps, schema_editor):
    # We get the model from the versioned app registry;
    # if we directly import it, it'll be the wrong version
    Partido = apps.get_model("parlamentares", "Partido")
    db_alias = schema_editor.connection.alias
    partidos = Partido.objects.all().exists()

    if partidos:
        print("Carga de Partido não efetuada. Já Existem partidos cadastrados...")
    else:
        Partido.objects.using(db_alias).bulk_create([
            Partido(sigla="PMDB",
                nome="PARTIDO DO MOVIMENTO DEMOCRÁTICO BRASILEIRO"),
            Partido(sigla="PTB",
                nome="PARTIDO TRABALHISTA BRASILEIRO"),
            Partido(sigla="PDT",
                nome="PARTIDO DEMOCRÁTICO TRABALHISTA"),
            Partido(sigla="PT",
                nome="PARTIDO DOS TRABALHADORES"),
            Partido(sigla="DEM",
                nome="DEMOCRATAS"),
            Partido(sigla="PCdoB",
                nome="PARTIDO COMUNISTA DO BRASIL"),
            Partido(sigla="PSB",
                nome="PARTIDO SOCIALISTA BRASILEIRO"),
            Partido(sigla="PSDB",
                nome="PARTIDO DA SOCIAL DEMOCRACIA BRASILEIRA"),
            Partido(sigla="PTC",
                nome="PARTIDO TRABALHISTA CRISTÃO"),
            Partido(sigla="PSC",
                nome="PARTIDO SOCIAL CRISTÃO"),
            Partido(sigla="PMN",
                nome="PARTIDO DA MOBILIZAÇÃO NACIONAL"),
            Partido(sigla="PRP",
                nome="PARTIDO REPUBLICANO PROGRESSISTA"),
            Partido(sigla="PPS",
                nome="PARTIDO POPULAR SOCIALISTA"),
            Partido(sigla="PV",
                nome="PARTIDO VERDE"),
            Partido(sigla="PTdoB",
                nome="PARTIDO TRABALHISTA DO BRASIL"),
            Partido(sigla="PP",
                nome="PARTIDO PROGRESSISTA"),
            Partido(sigla="PSTU",
                nome="PARTIDO SOCIALISTA DOS TRABALHADORES UNIFICADO"),
            Partido(sigla="PCB",
                nome="PARTIDO COMUNISTA BRASILEIRO"),
            Partido(sigla="PRTB",
                nome="PARTIDO RENOVADOR TRABALHISTA BRASILEIRO"),
            Partido(sigla="PHS",
                nome="PARTIDO HUMANISTA DA SOLIDARIEDADE"),
            Partido(sigla="PSDC",
                nome="PARTIDO SOCIAL DEMOCRATA CRISTÃO"),
            Partido(sigla="PCO",
                nome="PARTIDO DA CAUSA OPERÁRIA"),
            Partido(sigla="PODE",
                nome="PODEMOS"),
            Partido(sigla="PSL",
                nome="PARTIDO SOCIAL LIBERAL"),
            Partido(sigla="PRB",
                nome="PARTIDO REPUBLICANO BRASILEIRO"),
            Partido(sigla="PSOL",
                nome="PARTIDO SOCIALISMO E LIBERDADE"),
            Partido(sigla="PR",
                nome="PARTIDO DA REPÚBLICA"),
            Partido(sigla="PSD",
                nome="PARTIDO SOCIAL DEMOCRÁTICO"),
            Partido(sigla="PPL",
                nome="PARTIDO PÁTRIA LIVRE"),
            Partido(sigla="PEN",
                nome="PARTIDO ECOLÓGICO NACIONAL"),
            Partido(sigla="PROS",
                nome="PARTIDO REPUBLICANO DA ORDEM SOCIAL"),
            Partido(sigla="SD",
                nome="SOLIDARIEDADE"),
            Partido(sigla="NOVO",
                nome="PARTIDO NOVO"),
            Partido(sigla="REDE",
                nome="REDE SUSTENTABILIDADE"),
            Partido(sigla="PMB",
                nome="PARTIDO DA MULHER BRASILEIRA"),
           ])

class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0006_auto_20170831_1400'),
    ]

    operations = [
        migrations.RunPython(gera_partidos_tse),
    ]
