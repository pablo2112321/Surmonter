# Generated by Django 5.1.7 on 2025-06-23 05:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categoriasApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stock', models.IntegerField()),
                ('imagen', models.ImageField(upload_to='productos/')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='categoriasApp.categorias')),
            ],
        ),
    ]
