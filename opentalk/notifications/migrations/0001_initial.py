# Generated by Django 5.1.7 on 2025-03-18 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('like', 'Лайк'), ('comment', 'Комментарий'), ('follow', 'Подписка'), ('mention', 'Упоминание'), ('message', 'Сообщение'), ('repost', 'Репост'), ('system', 'Системное')], max_length=20, verbose_name='Тип')),
                ('content', models.TextField(verbose_name='Содержание')),
                ('reference_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID объекта')),
                ('reference_type', models.CharField(blank=True, max_length=50, null=True, verbose_name='Тип объекта')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('is_read', models.BooleanField(default=False, verbose_name='Прочитано')),
            ],
            options={
                'verbose_name': 'Уведомление',
                'verbose_name_plural': 'Уведомления',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PremiumSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_type', models.CharField(choices=[('monthly', 'Месячный'), ('yearly', 'Годовой')], max_length=20, verbose_name='Тип плана')),
                ('started_at', models.DateTimeField(verbose_name='Дата начала')),
                ('expires_at', models.DateTimeField(verbose_name='Дата окончания')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('payment_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='ID платежа')),
            ],
            options={
                'verbose_name': 'Премиум-подписка',
                'verbose_name_plural': 'Премиум-подписки',
                'ordering': ['-started_at'],
            },
        ),
    ]
