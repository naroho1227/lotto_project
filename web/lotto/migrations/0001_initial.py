from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LottoDraw',
            fields=[
                ('id',          models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('draw_number', models.IntegerField(unique=True)),
                ('numbers',     models.CharField(max_length=50)),
                ('bonus',       models.IntegerField()),
                ('draw_date',   models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='LottoTicket',
            fields=[
                ('id',           models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numbers',      models.CharField(max_length=50)),
                ('is_auto',      models.BooleanField(default=False)),
                ('purchased_at', models.DateTimeField(auto_now_add=True)),
                ('rank',         models.IntegerField(blank=True, null=True)),
                ('user',         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('draw',         models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='lotto.lottodraw')),
            ],
        ),
    ]
