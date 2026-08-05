import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0003_supportpointidempotencyrecord"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="contactchannel",
            name="contact_public_requires_authorization",
        ),
        migrations.RenameField(
            model_name="contactchannel",
            old_name="authorization_reference",
            new_name="source_reference",
        ),
        migrations.AddField(
            model_name="contactchannel",
            name="source_type",
            field=models.CharField(
                choices=[
                    ("consolidated_sheet", "Planilha consolidada"),
                    ("tourism_inventory", "Inventário turístico"),
                    ("other_public", "Outra fonte pública"),
                    ("legacy", "Registro legado"),
                ],
                default="legacy",
                max_length=32,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="contactchannel",
            name="verified_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="verified_contact_channels",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="contactchannel",
            constraint=models.CheckConstraint(
                condition=models.Q(("is_public", False))
                | (models.Q(("public_value__gt", "")) & models.Q(("source_reference__gt", ""))),
                name="contact_public_requires_provenance",
            ),
        ),
    ]
