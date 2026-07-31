import hashlib
import json
from dataclasses import dataclass
from typing import Any

from django.core.exceptions import ValidationError

from modules.core.models import EditorialStatus

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    EditorialStatus.DRAFT: frozenset({EditorialStatus.REVIEW, EditorialStatus.ARCHIVED}),
    EditorialStatus.REVIEW: frozenset({EditorialStatus.DRAFT, EditorialStatus.APPROVED}),
    EditorialStatus.APPROVED: frozenset({EditorialStatus.DRAFT, EditorialStatus.PUBLISHED}),
    EditorialStatus.PUBLISHED: frozenset({EditorialStatus.SUSPENDED, EditorialStatus.ARCHIVED}),
    EditorialStatus.SUSPENDED: frozenset(
        {EditorialStatus.DRAFT, EditorialStatus.PUBLISHED, EditorialStatus.ARCHIVED}
    ),
    EditorialStatus.ARCHIVED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class PublicationContext:
    editor_id: str
    reviewer_id: str
    publisher_id: str
    snapshot: dict[str, Any]
    critical_information_current: bool
    references_published: bool
    human_confirmed: bool = True


def validate_transition(current: str, target: str, *, reason: str = "") -> None:
    if current not in ALLOWED_TRANSITIONS:
        raise ValidationError({"current_status": "Estado editorial desconhecido."})
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ValidationError(
            {"target_status": f"Transição editorial inválida: {current} → {target}."}
        )
    if current == EditorialStatus.REVIEW and target == EditorialStatus.DRAFT and not reason.strip():
        raise ValidationError({"reason": "A devolução para rascunho exige um motivo."})


def validate_publication(context: PublicationContext) -> None:
    errors: dict[str, str] = {}
    if not context.snapshot:
        errors["snapshot"] = "A publicação exige um snapshot não vazio."
    if context.reviewer_id == context.publisher_id:
        errors["publisher_id"] = "Revisão e publicação exigem pessoas diferentes."
    if not context.critical_information_current:
        errors["critical_information"] = "Há informação crítica vencida."
    if not context.references_published:
        errors["references"] = "A versão referencia conteúdo ainda não publicado."
    if not context.human_confirmed:
        errors["human_confirmation"] = "Rascunhos automatizados exigem confirmação humana."
    if errors:
        raise ValidationError(errors)


def snapshot_checksum(snapshot: dict[str, Any]) -> str:
    canonical = json.dumps(
        snapshot,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
