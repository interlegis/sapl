from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0061_file_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='filemetadata',
            name='app_label',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='filemetadata',
            name='model_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='filemetadata',
            name='field_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='filemetadata',
            name='owner_pk',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='filemetadata',
            name='storage_name',
            field=models.CharField(editable=False, max_length=512, verbose_name='Storage name'),
        ),
        migrations.AddIndex(
            model_name='filemetadata',
            index=models.Index(
                fields=['app_label', 'model_name', 'field_name'],
                name='filemetadata_owner_context_idx',
            ),
        ),
    ]
