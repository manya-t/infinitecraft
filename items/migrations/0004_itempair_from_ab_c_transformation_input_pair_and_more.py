# Generated by Django 4.1.6 on 2024-03-22 18:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0003_item_emoji'),
    ]

    operations = [
        migrations.AddField(
            model_name='itempair',
            name='from_AB_C',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='to_other_pair', to='items.transformation'),
        ),
        migrations.AddField(
            model_name='transformation',
            name='input_pair',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='as_inputs', to='items.itempair'),
        ),
        migrations.AddConstraint(
            model_name='itempair',
            constraint=models.UniqueConstraint(fields=('first_input', 'second_input'), name='unique_pair'),
        ),
    ]