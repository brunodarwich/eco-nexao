import csv
import hashlib
import io
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.dateparse import parse_date, parse_datetime

MAX_CSV_BYTES = 10 * 1024 * 1024
MAX_CSV_ROWS = 10_000
MAX_RECORDED_ISSUES = 1_000

CATALOG_COLUMNS = (
    "external_id",
    "action",
    "record_status",
    "publish_status",
    "region_slug",
    "route_slugs",
    "route_role",
    "actor_kind",
    "category_slug",
    "subcategory",
    "public_name",
    "legal_name",
    "short_description",
    "full_description",
    "services",
    "street",
    "address_number",
    "address_extra",
    "neighborhood",
    "city",
    "state",
    "postal_code",
    "country_code",
    "latitude",
    "longitude",
    "phone_e164",
    "whatsapp_e164",
    "email",
    "website_url",
    "instagram_url",
    "opening_hours_text",
    "payment_methods",
    "accessibility_text",
    "languages",
    "image_url",
    "image_alt",
    "image_credit",
    "source_type",
    "source_reference",
    "verification_status",
    "verified_at",
    "verified_by",
    "public_contact_authorized",
    "media_authorized",
    "partnership_type",
    "admin_notes",
)

REQUIRED_COLUMNS = frozenset(
    {
        "external_id",
        "action",
        "record_status",
        "publish_status",
        "region_slug",
        "actor_kind",
        "category_slug",
        "public_name",
        "short_description",
        "city",
        "state",
        "country_code",
        "source_type",
        "source_reference",
        "verification_status",
        "public_contact_authorized",
        "media_authorized",
    }
)
ENUMS = {
    "action": {"upsert", "archive"},
    "record_status": {"active", "inactive"},
    "publish_status": {"draft", "review"},
    "actor_kind": {
        "business",
        "individual_provider",
        "community",
        "institution",
        "support",
    },
    "route_role": {"experience", "support", "start", "stop", "emergency", "service"},
    "source_type": {"inventory", "institutional", "direct", "field", "public_web", "mock"},
    "verification_status": {
        "unverified",
        "documental",
        "direct",
        "institutional",
        "field",
    },
    "public_contact_authorized": {"true", "false"},
    "media_authorized": {"true", "false"},
    "partnership_type": {"none", "institutional", "founding", "sponsored"},
}
E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
POSTAL_CODE_RE = re.compile(r"^(?:\d{5}-?\d{3}|\d{4,12})$")


@dataclass(frozen=True)
class CatalogRelationIndex:
    region_slugs: frozenset[str]
    category_slugs: frozenset[str]
    route_keys: frozenset[tuple[str, str]]
    actor_external_ids: frozenset[str] = frozenset()
    unavailable_actor_external_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    code: str
    line: int
    column: str | None
    message: str


@dataclass(frozen=True)
class CatalogPreviewRow:
    line: int
    external_id: str
    operation: str


@dataclass(frozen=True)
class CatalogCsvValidationResult:
    sha256: str
    row_count: int
    issues: tuple[ValidationIssue, ...]
    preview_rows: tuple[CatalogPreviewRow, ...] = ()
    normalized_rows: tuple[dict[str, str], ...] = ()
    issues_truncated: bool = False

    @property
    def error_count(self) -> int:
        return sum(issue.severity == "error" for issue in self.issues)

    @property
    def warning_count(self) -> int:
        return sum(issue.severity == "warning" for issue in self.issues)

    @property
    def valid(self) -> bool:
        return self.error_count == 0 and not self.issues_truncated


class _IssueCollector:
    def __init__(self) -> None:
        self.items: list[ValidationIssue] = []
        self.truncated = False

    def add(self, severity: str, code: str, line: int, column: str | None, message: str) -> None:
        if len(self.items) >= MAX_RECORDED_ISSUES:
            self.truncated = True
            return
        self.items.append(ValidationIssue(severity, code, line, column, message))


def _valid_https_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.username is None
        and parsed.password is None
    )


def _valid_iso_date(value: str) -> bool:
    try:
        return bool(parse_date(value) or parse_datetime(value))
    except ValueError:
        return False


def _validate_row(
    row: dict[str, str],
    line: int,
    relations: CatalogRelationIndex,
    issues: _IssueCollector,
    seen_external_ids: set[str],
) -> CatalogPreviewRow | None:
    def error(code: str, column: str, message: str) -> None:
        issues.add("error", code, line, column, message)

    def warning(code: str, column: str, message: str) -> None:
        issues.add("warning", code, line, column, message)

    for column in REQUIRED_COLUMNS:
        if not row[column]:
            error("required", column, "Campo obrigatório não informado.")
    for column, accepted in ENUMS.items():
        if row[column] and row[column] not in accepted:
            error("invalid_choice", column, "Valor fora do vocabulário permitido.")

    external_id = row["external_id"]
    if external_id in seen_external_ids:
        error("duplicate_external_id", "external_id", "Identificador duplicado no arquivo.")
    elif external_id:
        seen_external_ids.add(external_id)

    if external_id in relations.unavailable_actor_external_ids:
        error(
            "unknown_relation",
            "external_id",
            "Registro inexistente ou não autorizado.",
        )

    region_slug = row["region_slug"]
    if region_slug and region_slug not in relations.region_slugs:
        error("unknown_relation", "region_slug", "Região inexistente ou não autorizada.")
    if row["category_slug"] and row["category_slug"] not in relations.category_slugs:
        error("unknown_relation", "category_slug", "Categoria inexistente.")

    route_slugs = [slug.strip() for slug in row["route_slugs"].split("|") if slug.strip()]
    if len(route_slugs) != len(set(route_slugs)):
        warning("duplicate_relation", "route_slugs", "A mesma rota foi informada mais de uma vez.")
    for route_slug in set(route_slugs):
        if (region_slug, route_slug) not in relations.route_keys:
            error("unknown_relation", "route_slugs", "Rota inexistente ou não autorizada.")

    latitude, longitude = row["latitude"], row["longitude"]
    if bool(latitude) != bool(longitude):
        error("coordinate_pair", "latitude", "Latitude e longitude devem ser informadas juntas.")
    for column, minimum, maximum in (
        ("latitude", -90, 90),
        ("longitude", -180, 180),
    ):
        if row[column]:
            try:
                coordinate = float(row[column])
            except ValueError:
                error("invalid_number", column, "Coordenada inválida.")
            else:
                if not minimum <= coordinate <= maximum:
                    error("out_of_range", column, "Coordenada fora do intervalo permitido.")

    for column in ("phone_e164", "whatsapp_e164"):
        if row[column] and not E164_RE.fullmatch(row[column]):
            error("invalid_e164", column, "Telefone deve usar o formato E.164.")
    if row["email"]:
        try:
            validate_email(row["email"])
        except ValidationError:
            error("invalid_email", "email", "E-mail inválido.")
    for column in ("website_url", "instagram_url", "image_url"):
        if row[column] and not _valid_https_url(row[column]):
            error("invalid_https_url", column, "URL HTTPS pública inválida.")

    if row["state"] and not re.fullmatch(r"[A-Z]{2}", row["state"]):
        error("invalid_state", "state", "Estado deve usar duas letras maiúsculas.")
    if row["country_code"] and not re.fullmatch(r"[A-Z]{2}", row["country_code"]):
        error("invalid_country_code", "country_code", "País deve usar ISO alfa-2.")
    if row["postal_code"] and not POSTAL_CODE_RE.fullmatch(row["postal_code"]):
        error("invalid_postal_code", "postal_code", "Código postal inválido.")

    if row["image_url"] and (not row["image_alt"] or not row["image_credit"]):
        error("incomplete_media", "image_url", "Imagem exige texto alternativo e crédito.")
    if row["verification_status"] not in {"", "unverified"}:
        if not row["verified_at"] or not row["verified_by"]:
            error(
                "incomplete_verification",
                "verification_status",
                "Verificação exige data e responsável.",
            )
    if row["verified_at"] and not _valid_iso_date(row["verified_at"]):
        error("invalid_date", "verified_at", "Data de verificação inválida.")

    contacts = ("phone_e164", "whatsapp_e164", "email", "website_url", "instagram_url")
    if (
        row["publish_status"] == "review"
        and any(row[column] for column in contacts)
        and row["public_contact_authorized"] == "false"
    ):
        error(
            "contact_not_authorized",
            "public_contact_authorized",
            "Contato em revisão exige autorização pública.",
        )

    if len(row["short_description"]) > 180:
        warning("description_too_long", "short_description", "Descrição excede 180 caracteres.")
    if row["street"] and not latitude:
        warning("address_without_coordinates", "latitude", "Endereço sem coordenadas.")
    if not any(row[column] for column in contacts):
        warning("missing_contact", "public_name", "Registro sem contato público.")
    if not route_slugs:
        warning("missing_route", "route_slugs", "Registro não associado a uma rota.")
    if row["opening_hours_text"]:
        warning(
            "unstructured_opening_hours",
            "opening_hours_text",
            "Horário livre requer revisão editorial.",
        )

    if not external_id or external_id in relations.unavailable_actor_external_ids:
        return None
    if row["action"] == "archive":
        if external_id not in relations.actor_external_ids:
            error(
                "invalid_archive_target",
                "external_id",
                "Registro inexistente ou não autorizado para arquivamento.",
            )
            return None
        operation = "archive"
    elif row["action"] == "upsert":
        operation = "update" if external_id in relations.actor_external_ids else "create"
    else:
        return None
    return CatalogPreviewRow(line=line, external_id=external_id, operation=operation)


def validate_catalog_csv(
    content: bytes,
    relations: CatalogRelationIndex,
) -> CatalogCsvValidationResult:
    digest = hashlib.sha256(content).hexdigest()
    issues = _IssueCollector()
    if len(content) > MAX_CSV_BYTES:
        issues.add("error", "file_too_large", 0, None, "Arquivo excede o limite de 10 MiB.")
        return CatalogCsvValidationResult(
            digest,
            0,
            tuple(issues.items),
            issues_truncated=issues.truncated,
        )
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        issues.add("error", "invalid_encoding", 0, None, "Arquivo deve usar UTF-8.")
        return CatalogCsvValidationResult(
            digest,
            0,
            tuple(issues.items),
            issues_truncated=issues.truncated,
        )

    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        header = next(reader, None)
        if header != list(CATALOG_COLUMNS):
            issues.add(
                "error",
                "invalid_header",
                1,
                None,
                "Cabeçalho deve corresponder exatamente ao template oficial.",
            )
            return CatalogCsvValidationResult(
                digest,
                0,
                tuple(issues.items),
                issues_truncated=issues.truncated,
            )

        row_count = 0
        seen_external_ids: set[str] = set()
        preview_rows: list[CatalogPreviewRow] = []
        normalized_rows: list[dict[str, str]] = []
        for line, values in enumerate(reader, start=2):
            row_count += 1
            if row_count > MAX_CSV_ROWS:
                issues.add("error", "too_many_rows", line, None, "Arquivo excede 10.000 linhas.")
                break
            if len(values) != len(CATALOG_COLUMNS):
                issues.add(
                    "error",
                    "invalid_column_count",
                    line,
                    None,
                    "Linha não possui a quantidade esperada de colunas.",
                )
                continue
            row = dict(zip(CATALOG_COLUMNS, (value.strip() for value in values), strict=True))
            preview_row = _validate_row(row, line, relations, issues, seen_external_ids)
            if preview_row is not None:
                preview_rows.append(preview_row)
            normalized_rows.append(row)
    except csv.Error:
        issues.add("error", "malformed_csv", 0, None, "Estrutura CSV inválida.")
        row_count = 0
        preview_rows = []
        normalized_rows = []

    result = CatalogCsvValidationResult(
        sha256=digest,
        row_count=row_count,
        issues=tuple(issues.items),
        preview_rows=tuple(preview_rows),
        normalized_rows=tuple(normalized_rows),
        issues_truncated=issues.truncated,
    )
    if not result.valid:
        return CatalogCsvValidationResult(
            digest,
            row_count,
            tuple(issues.items),
            issues_truncated=issues.truncated,
        )
    return result
