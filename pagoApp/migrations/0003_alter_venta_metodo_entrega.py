# Generated by Django 5.1.7 on 2025-07-03 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pagoApp', '0002_alter_venta_empresa_envio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='venta',
            name='metodo_entrega',
            field=models.CharField(choices=[('retiro', 'Retiro en tienda'), ('envio', 'Envío a domicilio')], max_length=20),
        ),
    ]
