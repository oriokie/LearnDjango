# Generated by Django 4.1.4 on 2023-02-01 19:19

from django.db import migrations, models
import tasks.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Statement', models.FileField(upload_to=tasks.models.overwrite_upload_to)),
                ('Cheques', models.FileField(upload_to=tasks.models.overwrite_upload_to)),
                ('Direct_Debit', models.FileField(upload_to=tasks.models.overwrite_upload_to)),
                ('EFTs', models.FileField(upload_to=tasks.models.overwrite_upload_to)),
            ],
        ),
    ]
