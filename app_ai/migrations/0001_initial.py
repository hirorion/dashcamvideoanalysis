# Generated by Django 2.2 on 2019-07-05 04:24

import django.contrib.postgres.fields.jsonb
import django.core.serializers.json
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AiMovie',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=512)),
                ('unique_name', models.CharField(max_length=512)),
                ('json_path', models.CharField(max_length=512)),
                ('user_movie_id', models.IntegerField(blank=True, default=None, null=True)),
            ],
            options={
                'db_table': 'ai_movies',
            },
        ),
        migrations.CreateModel(
            name='AiFrameObjectTags',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fno', models.IntegerField()),
                ('tag', django.contrib.postgres.fields.jsonb.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_ai.AiMovie')),
            ],
            options={
                'db_table': 'ai_frame_object_tags',
            },
        ),
        migrations.CreateModel(
            name='AiFrameObject',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fno', models.IntegerField()),
                ('tag', models.CharField(max_length=256)),
                ('score', models.FloatField()),
                ('pose_ground_center', models.FloatField(default=0)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_ai.AiMovie')),
            ],
            options={
                'db_table': 'ai_frame_objects',
            },
        ),
        migrations.CreateModel(
            name='AiFrameInfo',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fno', models.IntegerField()),
                ('speed', models.FloatField()),
                ('meta', django.contrib.postgres.fields.jsonb.JSONField(encoder=django.core.serializers.json.DjangoJSONEncoder)),
                ('movie', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_ai.AiMovie')),
            ],
            options={
                'db_table': 'ai_frame_info',
            },
        ),
    ]
