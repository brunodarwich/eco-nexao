import csv
import hashlib
import io
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from .catalog_csv import CATALOG_COLUMNS

LEGACY_COLUMNS = (
    "pagina",
    "categoria",
    "titulo",
    "coordenadas_geograficas",
    "endereco",
    "local",
    "telefone",
    "email",
    "instagram",
    "site",
    "funcionamento",
    "servicos_instalacoes",
    "forma_pagamento",
    "contingente",
    "projetos_sociais",
    "observacoes_criticas",
    "observacoes",
    "texto_bruto",
    "forma_de_acesso",
)

ENRICHED_COLUMNS = LEGACY_COLUMNS + (
    "id",
    "latitude",
    "longitude",
    "status_coord",
    "categoria_normalizada",
    "categoria_id",
    "dist_rota_m",
    "km_rota",
    "segmento_rota",
    "ponto_projetado_rota",
)

REVIEW_COLUMNS = (
    "prioridade",
    "codigo",
    "external_id",
    "titulo",
    "fonte",
    "referencia_fonte",
    "campo",
    "valor_atual",
    "acao_recomendada",
)

INSTITUTION_CATEGORIES = {
    "cartorios",
    "emergencia",
    "religioso",
    "saude",
    "servico_publico",
}
EMERGENCY_CATEGORIES = {"assistencia_veicular", "emergencia", "farmacia", "saude"}


class PindobalInventoryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ReviewItem:
    priority: str
    code: str
    external_id: str
    title: str
    source: str
    source_reference: str
    field: str
    current_value: str
    recommendation: str

    def as_row(self) -> dict[str, str]:
        return {
            "prioridade": self.priority,
            "codigo": self.code,
            "external_id": self.external_id,
            "titulo": self.title,
            "fonte": self.source,
            "referencia_fonte": self.source_reference,
            "campo": self.field,
            "valor_atual": self.current_value,
            "acao_recomendada": self.recommendation,
        }


@dataclass(frozen=True, slots=True)
class PindobalInventoryResult:
    canonical_rows: tuple[dict[str, str], ...]
    review_items: tuple[ReviewItem, ...]
    summary: dict[str, object]


def _decode_csv(content: bytes, expected_header: tuple[str, ...], label: str):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise PindobalInventoryError(f"{label}: o arquivo deve usar UTF-8.") from error
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if tuple(reader.fieldnames or ()) != expected_header:
            raise PindobalInventoryError(f"{label}: cabeçalho inesperado.")
        rows = []
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise PindobalInventoryError(f"{label}: linha {line} possui colunas excedentes.")
            rows.append({column: (row[column] or "").strip() for column in expected_header})
        return rows
    except csv.Error as error:
        raise PindobalInventoryError(f"{label}: estrutura CSV malformada.") from error


def _shared_fingerprint(row: dict[str, str]) -> str:
    payload = json.dumps(
        [row[column] for column in LEGACY_COLUMNS],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


def _ascii_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    return re.sub(r"[^a-z0-9]+", " ", normalized.encode("ascii", "ignore").decode()).strip()


def _source_for(row: dict[str, str]) -> tuple[str, str, str]:
    page = row["pagina"]
    if page.casefold().startswith("pesquisa google maps"):
        return "google_maps", "Google Maps", page
    if page.casefold().startswith("pesquisa de transporte"):
        return "public_web", "Pesquisa de transporte", f"{page}; registro {row['id']}"
    if page.isdigit():
        return (
            "institutional",
            "Inventário da Secretaria de Turismo",
            f"Inventário da Oferta Turística da Secretaria de Turismo; página {page}",
        )
    return "unknown", "Fonte não classificada", page or f"registro {row['id']}"


def _e164_candidates(value: str) -> list[str]:
    candidates = []
    for part in re.split(r"\s*/\s*", value):
        digits = re.sub(r"\D", "", part)
        if len(digits) in {10, 11}:
            candidates.append(f"+55{digits}")
        elif len(digits) in {12, 13} and digits.startswith("55"):
            candidates.append(f"+{digits}")
    return list(dict.fromkeys(candidates))


def _email_candidates(value: str) -> list[str]:
    candidates = re.findall(
        r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        value,
    )
    valid = []
    for candidate in candidates:
        try:
            validate_email(candidate)
        except ValidationError:
            continue
        valid.append(candidate)
    return list(dict.fromkeys(valid))


def _https_url(value: str) -> tuple[str, bool]:
    if not value:
        return "", False
    candidate = re.split(r"\s+|\s*\|\s*", value.strip(), maxsplit=1)[0].rstrip("/,")
    if candidate.startswith("www."):
        candidate = f"https://{candidate}"
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return "", True
    if parsed.scheme == "https" and parsed.netloc and not parsed.username and not parsed.password:
        return candidate, candidate != value.strip()
    return "", True


def _instagram_url(value: str) -> tuple[str, bool]:
    if not value:
        return "", False
    first = re.split(r"[\s,|]+", value.strip(), maxsplit=1)[0]
    if first.startswith("https://"):
        url, changed = _https_url(first)
        return (url if "instagram.com" in urlsplit(url).netloc else ""), changed
    username = first.removeprefix("@").strip("/,")
    if re.fullmatch(r"[A-Za-z0-9._]+", username):
        return f"https://www.instagram.com/{username}", first != value.strip()
    return "", True


def _postal_code(value: str) -> str:
    match = re.search(r"\b(\d{5})-?(\d{3})\b", value)
    return "" if match is None else "".join(match.groups())


def _city(value: str) -> str:
    folded = _ascii_key(value)
    if "belterra" in folded:
        return "Belterra"
    if "santarem" in folded:
        return "Santarém"
    return ""


def _actor_kind(category: str) -> str:
    if category in INSTITUTION_CATEGORIES:
        return "institution"
    if category in {"assistencia_veicular", "combustivel", "farmacia", "transporte"}:
        return "support"
    return "business"


def _route_role(category: str) -> str:
    if category in EMERGENCY_CATEGORIES:
        return "emergency"
    if category == "transporte":
        return "service"
    return "support"


def _haversine_meters(left: dict[str, str], right: dict[str, str]) -> float | None:
    try:
        lat1, lon1 = math.radians(float(left["latitude"])), math.radians(float(left["longitude"]))
        lat2, lon2 = math.radians(float(right["latitude"])), math.radians(float(right["longitude"]))
    except (TypeError, ValueError):
        return None
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6_371_000 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _review(
    items: list[ReviewItem],
    row: dict[str, str],
    source: str,
    source_reference: str,
    priority: str,
    code: str,
    field: str,
    value: str,
    recommendation: str,
) -> None:
    items.append(
        ReviewItem(
            priority,
            code,
            f"inventory:pindobal:{row['id']}",
            row["titulo"],
            source,
            source_reference,
            field,
            value,
            recommendation,
        )
    )


def _canonical_row(row: dict[str, str], source_type: str, source_reference: str):
    category = row["categoria_id"]
    phones = _e164_candidates(row["telefone"])
    emails = _email_candidates(row["email"])
    website, _ = _https_url(row["site"])
    instagram, _ = _instagram_url(row["instagram"])
    location = row["local"]
    summary_category = row["categoria_normalizada"] or row["categoria"]
    notes = [
        f"id_operacional={row['id']}",
        f"fonte_original={source_reference}",
        f"categoria_original={row['categoria']}",
        f"dist_rota_m={row['dist_rota_m'] or 'ausente'}",
        f"km_rota={row['km_rota'] or 'ausente'}",
        f"segmento_rota={row['segmento_rota'] or 'ausente'}",
    ]
    if row["telefone"]:
        notes.append(f"telefone_original={row['telefone']}")
    values = {
        "external_id": f"inventory:pindobal:{row['id']}",
        "action": "upsert",
        "record_status": "active",
        "publish_status": "draft",
        "region_slug": "santarem-alter-do-chao",
        "route_slugs": "pindobal",
        "route_role": _route_role(category),
        "actor_kind": _actor_kind(category),
        "category_slug": category,
        "subcategory": _ascii_key(row["categoria"]).replace(" ", "-")[:120],
        "public_name": row["titulo"],
        "legal_name": "",
        "short_description": (
            f"{summary_category.capitalize()} em {location}; informações importadas do inventário "
            "e pendentes de revisão editorial."
        )[:180],
        "full_description": "",
        "services": row["servicos_instalacoes"],
        "street": row["endereco"],
        "address_number": "",
        "address_extra": "",
        "neighborhood": "",
        "city": _city(location),
        "state": "PA",
        "postal_code": _postal_code(row["endereco"]),
        "country_code": "BR",
        "latitude": row["latitude"],
        "longitude": row["longitude"],
        "phone_e164": phones[0] if phones else "",
        "whatsapp_e164": "",
        "email": emails[0] if emails else "",
        "website_url": website,
        "instagram_url": instagram,
        "opening_hours_text": row["funcionamento"],
        "payment_methods": row["forma_pagamento"],
        "accessibility_text": "",
        "languages": "pt-BR",
        "image_url": "",
        "image_alt": "",
        "image_credit": "",
        "source_type": source_type,
        "source_reference": source_reference,
        "verification_status": "unverified",
        "verified_at": "",
        "verified_by": "",
        "public_contact_authorized": "false",
        "media_authorized": "false",
        "partnership_type": "none",
        "admin_notes": "; ".join(notes),
    }
    return {column: values[column] for column in CATALOG_COLUMNS}


def adapt_pindobal_inventory(raw_content: bytes, operational_content: bytes):
    raw_rows = _decode_csv(raw_content, LEGACY_COLUMNS, "Inventário histórico")
    operational_rows = _decode_csv(
        operational_content,
        ENRICHED_COLUMNS,
        "Complemento operacional",
    )
    raw_counts = Counter(_shared_fingerprint(row) for row in raw_rows)
    operational_counts = Counter(_shared_fingerprint(row) for row in operational_rows)
    if raw_counts != operational_counts:
        raw_only = sum((raw_counts - operational_counts).values())
        operational_only = sum((operational_counts - raw_counts).values())
        raise PindobalInventoryError(
            "As fontes divergem nos campos compartilhados "
            f"(somente histórico={raw_only}, somente operacional={operational_only})."
        )
    raw_by_fingerprint: dict[str, deque[dict[str, str]]] = defaultdict(deque)
    for row in raw_rows:
        raw_by_fingerprint[_shared_fingerprint(row)].append(row)

    ids = [row["id"] for row in operational_rows]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise PindobalInventoryError(
            "O complemento operacional possui identificador vazio ou repetido."
        )

    merged = []
    for operational in operational_rows:
        fingerprint = _shared_fingerprint(operational)
        raw = raw_by_fingerprint[fingerprint].popleft()
        merged.append({**raw, **operational})

    review_items: list[ReviewItem] = []
    canonical_rows = []
    source_counts: Counter[str] = Counter()
    quarantined = 0
    for row in merged:
        source_type, source, source_reference = _source_for(row)
        source_counts[source] += 1
        if source_type == "google_maps":
            quarantined += 1
            _review(
                review_items,
                row,
                source,
                source_reference,
                "bloqueante",
                "google_source_quarantine",
                "pagina",
                row["pagina"],
                "Confirmar em fonte independente ou diretamente com o responsável "
                "antes de criar rascunho.",
            )
            continue
        if source_type == "unknown":
            _review(
                review_items,
                row,
                source,
                source_reference,
                "alta",
                "unknown_source",
                "pagina",
                row["pagina"],
                "Identificar a fonte antes da revisão editorial.",
            )

        phones = _e164_candidates(row["telefone"])
        emails = _email_candidates(row["email"])
        website, website_changed = _https_url(row["site"])
        instagram, instagram_changed = _instagram_url(row["instagram"])
        if not row["latitude"] or not row["longitude"]:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "alta",
                "missing_coordinates",
                "coordenadas",
                "",
                "Georreferenciar ou definir área de atendimento antes da publicação.",
            )
        if not row["endereco"]:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "missing_address",
                "endereco",
                "",
                "Confirmar endereço ou indicar atendimento móvel.",
            )
        if not any((row["telefone"], row["email"], row["instagram"], row["site"])):
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "missing_contact",
                "contatos",
                "",
                "Confirmar ao menos um canal público autorizado.",
            )
        else:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "alta",
                "contact_authorization_required",
                "contatos",
                row["telefone"] or row["email"] or row["instagram"] or row["site"],
                "Registrar autorização antes de tornar qualquer contato público.",
            )
        if row["telefone"] and not phones:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "alta",
                "phone_not_normalized",
                "telefone",
                row["telefone"],
                "Corrigir manualmente; o valor não pôde ser convertido com segurança para E.164.",
            )
        elif len(phones) > 1:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "multiple_phones",
                "telefone",
                row["telefone"],
                "Escolher o telefone principal e classificar telefone/WhatsApp.",
            )
        if row["email"] and not emails:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "alta",
                "invalid_email",
                "email",
                row["email"],
                "Confirmar e informar um e-mail válido.",
            )
        elif len(emails) > 1:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "multiple_emails",
                "email",
                row["email"],
                "Escolher o e-mail público principal.",
            )
        elif row["email"] and emails[0] != row["email"].strip():
            _review(
                review_items,
                row,
                source,
                source_reference,
                "baixa",
                "email_cleaned",
                "email",
                row["email"],
                f"Confirmar o e-mail normalizado: {emails[0]}",
            )
        if row["site"] and not website:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "alta",
                "invalid_website",
                "site",
                row["site"],
                "Confirmar e informar uma URL HTTPS válida.",
            )
        elif row["site"] and website_changed:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "baixa",
                "website_cleaned",
                "site",
                row["site"],
                f"Confirmar a URL normalizada: {website}",
            )
        if row["instagram"] and not instagram:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "invalid_instagram",
                "instagram",
                row["instagram"],
                "Confirmar o usuário e informar a URL HTTPS completa.",
            )
        elif row["instagram"] and instagram_changed:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "baixa",
                "instagram_cleaned",
                "instagram",
                row["instagram"],
                f"Confirmar a URL normalizada: {instagram}",
            )
        try:
            distance = float(row["dist_rota_m"])
        except ValueError:
            distance = None
        if distance is None:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "missing_route_projection",
                "dist_rota_m",
                row["dist_rota_m"],
                "Recalcular a relação espacial com a geometria vigente da rota.",
            )
        elif distance > 500:
            _review(
                review_items,
                row,
                source,
                source_reference,
                "média",
                "far_from_route",
                "dist_rota_m",
                row["dist_rota_m"],
                "Confirmar se o ponto deve permanecer vinculado à rota de Pindobal.",
            )
        canonical_rows.append(_canonical_row(row, source_type, source_reference))

    duplicate_pairs = set()
    shared_contact_pairs = set()
    for index, left in enumerate(merged):
        for right in merged[index + 1 :]:
            same_title = _ascii_key(left["titulo"]) == _ascii_key(right["titulo"])
            same_address = bool(left["endereco"]) and _ascii_key(left["endereco"]) == _ascii_key(
                right["endereco"]
            )
            distance = _haversine_meters(left, right)
            if same_title and (same_address or (distance is not None and distance <= 100)):
                pair = tuple(sorted((left["id"], right["id"])))
                if pair in duplicate_pairs:
                    continue
                duplicate_pairs.add(pair)
                for row in (left, right):
                    _, source, source_reference = _source_for(row)
                    other_id = pair[0] if row["id"] == pair[1] else pair[1]
                    _review(
                        review_items,
                        row,
                        source,
                        source_reference,
                        "alta",
                        "possible_duplicate",
                        "titulo",
                        row["titulo"],
                        f"Comparar manualmente com o registro inventory:pindobal:{other_id}.",
                    )
            left_contacts = set(_e164_candidates(left["telefone"])) | set(
                _email_candidates(left["email"])
            )
            right_contacts = set(_e164_candidates(right["telefone"])) | set(
                _email_candidates(right["email"])
            )
            shared_contacts = sorted(left_contacts & right_contacts)
            pair = tuple(sorted((left["id"], right["id"])))
            if shared_contacts and pair not in duplicate_pairs and pair not in shared_contact_pairs:
                shared_contact_pairs.add(pair)
                for row in (left, right):
                    _, source, source_reference = _source_for(row)
                    other_id = pair[0] if row["id"] == pair[1] else pair[1]
                    _review(
                        review_items,
                        row,
                        source,
                        source_reference,
                        "média",
                        "shared_contact_candidate",
                        "contatos",
                        " | ".join(shared_contacts),
                        "Confirmar se pertence ao mesmo ator do registro "
                        f"inventory:pindobal:{other_id} ou se é contato compartilhado.",
                    )

    priority_counts = Counter(item.priority for item in review_items)
    code_counts = Counter(item.code for item in review_items)
    category_counts = Counter(row["category_slug"] for row in canonical_rows)
    summary = {
        "raw_sha256": hashlib.sha256(raw_content).hexdigest(),
        "operational_sha256": hashlib.sha256(operational_content).hexdigest(),
        "raw_rows": len(raw_rows),
        "operational_rows": len(operational_rows),
        "merged_records": len(merged),
        "collapsed_shared_rows": len(merged),
        "canonical_drafts": len(canonical_rows),
        "quarantined_google_rows": quarantined,
        "possible_duplicate_pairs": len(duplicate_pairs),
        "shared_contact_pairs": len(shared_contact_pairs),
        "review_items": len(review_items),
        "review_records": len({item.external_id for item in review_items}),
        "source_counts": dict(sorted(source_counts.items())),
        "category_counts": dict(sorted(category_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "review_code_counts": dict(sorted(code_counts.items())),
    }
    return PindobalInventoryResult(tuple(canonical_rows), tuple(review_items), summary)


def _csv_text(columns: tuple[str, ...], rows) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def write_pindobal_inventory_outputs(result: PindobalInventoryResult, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = output_dir / "catalogo-pindobal-adequado.csv"
    review_path = output_dir / "revisao-manual-pindobal.csv"
    summary_path = output_dir / "resumo-pindobal.json"
    catalog_path.write_text(
        _csv_text(CATALOG_COLUMNS, result.canonical_rows),
        encoding="utf-8-sig",
        newline="",
    )
    review_path.write_text(
        _csv_text(REVIEW_COLUMNS, (item.as_row() for item in result.review_items)),
        encoding="utf-8-sig",
        newline="",
    )
    summary_path.write_text(
        json.dumps(result.summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return catalog_path, review_path, summary_path
