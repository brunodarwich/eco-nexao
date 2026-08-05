from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("analytics", "0002_enable_rls")]

    operations = [
        migrations.AlterField(
            "rawanalyticsevent",
            "anonymous_id",
            models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            "rawanalyticsevent",
            "session_id",
            models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AlterField(
            "rawanalyticsevent",
            "consent_id",
            models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            "dailyanalyticsaggregate",
            "support_point_id",
            models.CharField(blank=True, db_index=True, default="", max_length=36),
        ),
        migrations.AlterUniqueTogether(
            name="dailyanalyticsaggregate",
            unique_together={
                ("date", "event_name", "region_slug", "route_slug", "support_point_id")
            },
        ),
    ]
