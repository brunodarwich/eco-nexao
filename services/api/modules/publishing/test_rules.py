import pytest
from django.core.exceptions import ValidationError

from modules.core.models import EditorialStatus
from modules.publishing.rules import (
    PublicationContext,
    snapshot_checksum,
    validate_publication,
    validate_transition,
)


def valid_context(**overrides) -> PublicationContext:
    values = {
        "editor_id": "editor-1",
        "reviewer_id": "reviewer-1",
        "publisher_id": "publisher-1",
        "snapshot": {"slug": "rota-do-rio", "name": "Rota do Rio"},
        "critical_information_current": True,
        "references_published": True,
        "human_confirmed": True,
    }
    values.update(overrides)
    return PublicationContext(**values)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (EditorialStatus.DRAFT, EditorialStatus.REVIEW),
        (EditorialStatus.REVIEW, EditorialStatus.APPROVED),
        (EditorialStatus.APPROVED, EditorialStatus.PUBLISHED),
        (EditorialStatus.PUBLISHED, EditorialStatus.SUSPENDED),
        (EditorialStatus.SUSPENDED, EditorialStatus.PUBLISHED),
    ],
)
def test_valid_editorial_transitions(current, target):
    validate_transition(current, target)


def test_review_return_requires_reason():
    with pytest.raises(ValidationError, match="exige um motivo"):
        validate_transition(EditorialStatus.REVIEW, EditorialStatus.DRAFT)

    validate_transition(
        EditorialStatus.REVIEW,
        EditorialStatus.DRAFT,
        reason="Fonte precisa ser atualizada.",
    )


def test_invalid_editorial_transition_is_rejected():
    with pytest.raises(ValidationError, match="Transição editorial inválida"):
        validate_transition(EditorialStatus.DRAFT, EditorialStatus.PUBLISHED)


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"snapshot": {}}, "snapshot não vazio"),
        ({"publisher_id": "reviewer-1"}, "pessoas diferentes"),
        ({"critical_information_current": False}, "informação crítica vencida"),
        ({"references_published": False}, "conteúdo ainda não publicado"),
        ({"human_confirmed": False}, "confirmação humana"),
    ],
)
def test_publication_invariants_are_enforced(override, message):
    with pytest.raises(ValidationError, match=message):
        validate_publication(valid_context(**override))


def test_valid_publication_context_passes():
    validate_publication(valid_context())


def test_snapshot_checksum_is_stable_for_key_order():
    first = snapshot_checksum({"name": "Pindobal", "position": 1})
    second = snapshot_checksum({"position": 1, "name": "Pindobal"})

    assert first == second
    assert len(first) == 64
