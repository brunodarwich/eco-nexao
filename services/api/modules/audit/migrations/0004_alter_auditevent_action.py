from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("audit", "0003_alter_auditevent_action")]

    operations = [
        migrations.AlterField(
            model_name="auditevent",
            name="action",
            field=models.CharField(
                choices=[
                    ("auth.login", "Login administrativo"),
                    ("auth.logout", "Logout administrativo"),
                    ("editorial.approve", "Aprovação editorial"),
                    ("publication.publish", "Publicação"),
                    ("publication.restore", "Restauração"),
                    ("external.discovery", "Descoberta externa"),
                    ("import.commit", "Confirmação de importação"),
                    ("report.moderate", "Moderação de relato"),
                    ("catalog.support_point.create", "Cadastro de ponto de apoio"),
                ],
                db_index=True,
                max_length=64,
            ),
        )
    ]
