import uuid

from django.db import models


class UUIDTimeStampedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EditorialStatus(models.TextChoices):
    DRAFT = "draft", "Rascunho"
    REVIEW = "review", "Em revisão"
    APPROVED = "approved", "Aprovado"
    PUBLISHED = "published", "Publicado"
    SUSPENDED = "suspended", "Suspenso"
    ARCHIVED = "archived", "Arquivado"
