# Generated by Django 2.0.6 on 2018-06-06 23:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gitmate_config', '0024_delete_plugin_model'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repository',
            name='org',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repos', to='gitmate_config.Organization'),
        ),
    ]
