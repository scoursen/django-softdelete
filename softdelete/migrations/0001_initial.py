# Generated by Django 5.0.7 on 2024-09-24 13:11

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChangeSet",
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
                    "created_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("object_id", models.CharField(max_length=100)),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SoftDeleteRecord",
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
                    "created_date",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("object_id", models.CharField(max_length=100)),
                (
                    "changeset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="soft_delete_records",
                        to="softdelete.changeset",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="changeset",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="softdelete__content_7eb5a8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="softdeleterecord",
            index=models.Index(
                fields=["content_type", "object_id"],
                name="softdelete__content_faa170_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="softdeleterecord",
            unique_together={("changeset", "content_type", "object_id")},
        ),
    ]
