# Generated by Django 2.0.6 on 2018-07-10 13:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('gitmate_config', '0025_auto_20180606_2301'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conflicts_label', models.CharField(default='needs rebase', help_text='Label for pull requests that have merge conflicts.', max_length=25)),
                ('conflicts_message', models.CharField(default='This PR has merge conflicts, please do a manual rebase and resolve conflicts.', help_text='Message to be returned if there are merge conflicts in the pull request.', max_length=1500)),
                ('repo', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='gitmate_pr_conflicts_notifier_settings', to='gitmate_config.Repository')),
            ],
            options={
                'verbose_name_plural': 'settings',
                'abstract': False,
            },
        ),
    ]
