from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('base', '0061_casalegislativa_informacao_geral')]

    operations = [
        migrations.CreateModel(
            name='AtualizacaoConteudoPublico',
            fields=[
                ('chave', models.CharField(
                    max_length=100, primary_key=True, serialize=False)),
                ('timestamp', models.DateTimeField(
                    blank=True, db_index=True, null=True)),
                ('origem', models.CharField(blank=True, max_length=100)),
                ('objeto_id', models.CharField(blank=True, max_length=100)),
                ('disponivel_em', models.DateField(
                    blank=True, db_index=True, null=True)),
            ],
            options={'verbose_name': 'Atualização do conteúdo público'},
        ),
    ]
