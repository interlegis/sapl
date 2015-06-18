# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comissoes', '0001_initial'),
        ('parlamentares', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcompMateria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('endereco_email', models.CharField(max_length=100)),
                ('txt_hash', models.CharField(max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='Anexada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_anexacao', models.DateField()),
                ('data_desanexacao', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssuntoMateria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_assunto', models.CharField(max_length=200)),
                ('descricao_dispositivo', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_autor', models.CharField(max_length=50, null=True, blank=True)),
                ('descricao_cargo', models.CharField(max_length=50, null=True, blank=True)),
                ('col_username', models.CharField(max_length=50, null=True, blank=True)),
                ('comissao', models.ForeignKey(blank=True, to='comissoes.Comissao', null=True)),
                ('parlamentar', models.ForeignKey(blank=True, to='parlamentares.Parlamentar', null=True)),
                ('partido', models.ForeignKey(blank=True, to='parlamentares.Partido', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Autoria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('primeiro_autor', models.BooleanField()),
                ('autor', models.ForeignKey(to='materia.Autor')),
            ],
        ),
        migrations.CreateModel(
            name='DespachoInicial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField()),
                ('comissao', models.ForeignKey(to='comissoes.Comissao')),
            ],
        ),
        migrations.CreateModel(
            name='DocumentoAcessorio',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_documento', models.CharField(max_length=30)),
                ('data_documento', models.DateField(null=True, blank=True)),
                ('nome_autor_documento', models.CharField(max_length=50, null=True, blank=True)),
                ('txt_ementa', models.TextField(null=True, blank=True)),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='MateriaAssunto',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assunto', models.ForeignKey(to='materia.AssuntoMateria')),
            ],
        ),
        migrations.CreateModel(
            name='MateriaLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_protocolo', models.IntegerField(null=True, blank=True)),
                ('numero_ident_basica', models.IntegerField()),
                ('ano_ident_basica', models.SmallIntegerField()),
                ('data_apresentacao', models.DateField(null=True, blank=True)),
                ('tipo_apresentacao', models.CharField(max_length=1, null=True, blank=True)),
                ('data_publicacao', models.DateField(null=True, blank=True)),
                ('numero_origem_externa', models.CharField(max_length=5, null=True, blank=True)),
                ('ano_origem_externa', models.SmallIntegerField(null=True, blank=True)),
                ('data_origem_externa', models.DateField(null=True, blank=True)),
                ('nome_apelido', models.CharField(max_length=50, null=True, blank=True)),
                ('numero_dias_prazo', models.IntegerField(null=True, blank=True)),
                ('data_fim_prazo', models.DateField(null=True, blank=True)),
                ('indicador_tramitacao', models.BooleanField()),
                ('polemica', models.NullBooleanField()),
                ('descricao_objeto', models.CharField(max_length=150, null=True, blank=True)),
                ('complementar', models.NullBooleanField()),
                ('txt_ementa', models.TextField()),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('txt_resultado', models.TextField(null=True, blank=True)),
                ('anexadas', models.ManyToManyField(related_name='anexo_de', through='materia.Anexada', to='materia.MateriaLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='Numeracao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_ordem', models.IntegerField()),
                ('numero_materia', models.CharField(max_length=5)),
                ('ano_materia', models.SmallIntegerField()),
                ('data_materia', models.DateField(null=True, blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='Orgao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome_orgao', models.CharField(max_length=60)),
                ('sigla_orgao', models.CharField(max_length=10)),
                ('unid_deliberativa', models.BooleanField()),
                ('endereco_orgao', models.CharField(max_length=100, null=True, blank=True)),
                ('numero_tel_orgao', models.CharField(max_length=50, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Origem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_origem', models.CharField(max_length=10)),
                ('nome_origem', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Parecer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_conclusao', models.CharField(max_length=3, null=True, blank=True)),
                ('tipo_apresentacao', models.CharField(max_length=1)),
                ('txt_parecer', models.TextField(null=True, blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='Proposicao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_envio', models.DateTimeField()),
                ('data_recebimento', models.DateTimeField(null=True, blank=True)),
                ('txt_descricao', models.CharField(max_length=100)),
                ('cod_mat_ou_doc', models.IntegerField(null=True, blank=True)),
                ('data_devolucao', models.DateTimeField(null=True, blank=True)),
                ('txt_justif_devolucao', models.CharField(max_length=200, null=True, blank=True)),
                ('numero_proposicao', models.IntegerField(null=True, blank=True)),
                ('autor', models.ForeignKey(to='materia.Autor')),
                ('materia', models.ForeignKey(blank=True, to='materia.MateriaLegislativa', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegimeTramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_regime_tramitacao', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Relatoria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_desig_relator', models.DateField()),
                ('data_destit_relator', models.DateField(null=True, blank=True)),
                ('comissao', models.ForeignKey(blank=True, to='comissoes.Comissao', null=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('parlamentar', models.ForeignKey(to='parlamentares.Parlamentar')),
            ],
        ),
        migrations.CreateModel(
            name='StatusTramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_status', models.CharField(max_length=10)),
                ('descricao_status', models.CharField(max_length=60)),
                ('fim_tramitacao', models.BooleanField()),
                ('retorno_tramitacao', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='TipoAutor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_autor', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='TipoDocumento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_documento', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='TipoFimRelatoria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_fim_relatoria', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='TipoMateriaLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sigla_tipo_materia', models.CharField(max_length=5)),
                ('descricao_tipo_materia', models.CharField(max_length=50)),
                ('num_automatica', models.BooleanField()),
                ('quorum_minimo_votacao', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='TipoProposicao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_tipo_proposicao', models.CharField(max_length=50)),
                ('mat_ou_doc', models.BooleanField()),
                ('tipo_mat_ou_doc', models.IntegerField()),
                ('nome_modelo', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Tramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data_tramitacao', models.DateField(null=True, blank=True)),
                ('data_encaminha', models.DateField(null=True, blank=True)),
                ('ult_tramitacao', models.BooleanField()),
                ('urgencia', models.BooleanField()),
                ('sigla_turno', models.CharField(max_length=1, null=True, blank=True)),
                ('txt_tramitacao', models.TextField(null=True, blank=True)),
                ('data_fim_prazo', models.DateField(null=True, blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('status', models.ForeignKey(blank=True, to='materia.StatusTramitacao', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UnidadeTramitacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comissao', models.ForeignKey(blank=True, to='comissoes.Comissao', null=True)),
                ('orgao', models.ForeignKey(blank=True, to='materia.Orgao', null=True)),
                ('parlamentar', models.ForeignKey(blank=True, to='parlamentares.Parlamentar', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unid_tram_dest',
            field=models.ForeignKey(related_name='+', blank=True, to='materia.UnidadeTramitacao', null=True),
        ),
        migrations.AddField(
            model_name='tramitacao',
            name='unid_tram_local',
            field=models.ForeignKey(related_name='+', blank=True, to='materia.UnidadeTramitacao', null=True),
        ),
        migrations.AddField(
            model_name='relatoria',
            name='tipo_fim_relatoria',
            field=models.ForeignKey(blank=True, to='materia.TipoFimRelatoria', null=True),
        ),
        migrations.AddField(
            model_name='proposicao',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoProposicao'),
        ),
        migrations.AddField(
            model_name='parecer',
            name='relatoria',
            field=models.ForeignKey(to='materia.Relatoria'),
        ),
        migrations.AddField(
            model_name='numeracao',
            name='tipo_materia',
            field=models.ForeignKey(to='materia.TipoMateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='local_origem_externa',
            field=models.ForeignKey(blank=True, to='materia.Origem', null=True),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='regime_tramitacao',
            field=models.ForeignKey(to='materia.RegimeTramitacao'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='tipo_id_basica',
            field=models.ForeignKey(to='materia.TipoMateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='materialegislativa',
            name='tipo_origem_externa',
            field=models.ForeignKey(related_name='+', blank=True, to='materia.TipoMateriaLegislativa', null=True),
        ),
        migrations.AddField(
            model_name='materiaassunto',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='documentoacessorio',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='documentoacessorio',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoDocumento'),
        ),
        migrations.AddField(
            model_name='despachoinicial',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='autoria',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='autor',
            name='tipo',
            field=models.ForeignKey(to='materia.TipoAutor'),
        ),
        migrations.AddField(
            model_name='anexada',
            name='materia_anexada',
            field=models.ForeignKey(related_name='+', to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='anexada',
            name='materia_principal',
            field=models.ForeignKey(related_name='+', to='materia.MateriaLegislativa'),
        ),
        migrations.AddField(
            model_name='acompmateria',
            name='materia',
            field=models.ForeignKey(to='materia.MateriaLegislativa'),
        ),
    ]
