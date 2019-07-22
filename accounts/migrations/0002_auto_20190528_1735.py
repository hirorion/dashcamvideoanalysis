# Generated by Django 2.2 on 2019-05-28 08:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_admin', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='contract_company',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='app_admin.ContractCompany'),
        ),
        migrations.AddField(
            model_name='users',
            name='contract_company_user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='app_admin.ContractCompanyUser'),
        ),
        migrations.AddField(
            model_name='users',
            name='irric_user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='app_admin.IrricUser'),
        ),
        migrations.AddField(
            model_name='users',
            name='user_group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounts.UserGroup'),
        ),
    ]
