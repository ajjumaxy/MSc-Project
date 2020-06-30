# Generated by Django 3.0.6 on 2020-06-29 12:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tables_daniel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='companytable',
            name='Company',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='companytable',
            name='CompanyID',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='Country',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='Industry',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='ListedOn',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='NoEmployees',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='Revenue',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='Sector',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='companytable',
            name='Symbol',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='AdviceToManagement',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Company',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='CompanyID',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='tables_daniel.CompanyTable'),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Cons',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Contract',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='ContractPeriod',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Day',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='EmployeeRelationship',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='JobTitle',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Location',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Month',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='OpinionOfCEO',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Outlook',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Pros',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Recommendation',
            field=models.CharField(blank=True, max_length=25),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='ReviewTitle',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='glassdoortable',
            name='Year',
            field=models.IntegerField(null=True),
        ),
    ]