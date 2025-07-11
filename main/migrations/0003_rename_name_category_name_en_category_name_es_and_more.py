# Generated by Django 5.2.1 on 2025-06-01 10:20

from django.db import migrations, models


def initialize_categories(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    categories = [
        Category(
            name_es='Programación',
            name_en='Programing',
            slug='programing',
            color='#4643ec'
        ),
        Category(
            name_es='Seguridad',
            name_en='Security',
            slug='security',
            color='#de47e2'
        ),
        Category(
            name_es='Deportes',
            name_en='Sports',
            slug='sports',
            color='#3eb99a'
        ),
        Category(
            name_es='Juegos',
            name_en='Games',
            slug='games',
            color='#ff4500'
        ),
        Category(
            name_es='Finanzas',
            name_en='Finance',
            slug='finance',
            color='#f14979'
        ),
        Category(
            name_es='Ciencia',
            name_en='Science',
            slug='science',
            color='var(--dark-gray)'
        ),
    ]
    Category.objects.bulk_create(categories)


def reverse_initialize_categories(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_post_slug'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='name',
            new_name='name_en',
        ),
        migrations.AddField(
            model_name='category',
            name='name_es',
            field=models.CharField(default='linux', max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='slug',
            field=models.SlugField(default=1, max_length=120, unique=True),
            preserve_default=False,
        ),
        migrations.RunPython(initialize_categories, reverse_initialize_categories),
        migrations.AlterField(
            model_name='post',
            name='description_en',
            field=models.CharField(max_length=160),
        ),
        migrations.AlterField(
            model_name='post',
            name='description_es',
            field=models.CharField(max_length=160),
        ),
        migrations.AlterField(
            model_name='post',
            name='title_en',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='post',
            name='title_es',
            field=models.CharField(max_length=60),
        ),
    ]
