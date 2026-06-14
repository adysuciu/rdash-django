from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="JamStorageSyncState",
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
                (
                    "last_successful_sync_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("imported", models.PositiveIntegerField(default=0)),
                ("updated", models.PositiveIntegerField(default=0)),
                ("skipped", models.PositiveIntegerField(default=0)),
                ("last_error", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Jam storage sync state",
                "verbose_name_plural": "Jam storage sync state",
            },
        ),
        migrations.CreateModel(
            name="JamJar",
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
                ("sheet_id", models.CharField(max_length=80, unique=True)),
                ("jam_type", models.CharField(blank=True, max_length=120)),
                ("fruit", models.CharField(blank=True, max_length=120)),
                (
                    "year",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        db_index=True,
                        null=True,
                    ),
                ),
                (
                    "origin",
                    models.CharField(blank=True, db_index=True, max_length=120),
                ),
                ("big", models.BooleanField(db_index=True, default=False)),
                (
                    "status",
                    models.CharField(blank=True, db_index=True, max_length=120),
                ),
                ("date", models.DateField(blank=True, db_index=True, null=True)),
                ("raw_data", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-date", "-year", "sheet_id"],
                "indexes": [
                    models.Index(
                        fields=["jam_type"],
                        name="jams_jamjar_jam_typ_c1f45a_idx",
                    ),
                    models.Index(
                        fields=["fruit"],
                        name="jams_jamjar_fruit_dfb976_idx",
                    ),
                ],
            },
        ),
    ]
