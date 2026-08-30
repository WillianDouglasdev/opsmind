from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActionItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("recommendation_key", models.CharField(max_length=100)),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("source_alert_key", models.CharField(max_length=120)),
                ("source_alert_type", models.CharField(max_length=64)),
                (
                    "priority",
                    models.CharField(
                        choices=[
                            ("low", "Baixa"),
                            ("medium", "Média"),
                            ("high", "Alta"),
                            ("critical", "Crítica"),
                        ],
                        max_length=12,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pendente"),
                            ("in_progress", "Em andamento"),
                            ("completed", "Concluída"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Item de ação",
                "verbose_name_plural": "Itens de ação",
                "ordering": ["-created_at"],
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(
                            ("status__in", ["pending", "in_progress"])
                        ),
                        fields=("source_alert_key", "recommendation_key"),
                        name="unique_open_action_recommendation",
                    )
                ],
            },
        ),
    ]
