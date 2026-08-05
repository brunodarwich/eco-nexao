import math
import re
from collections.abc import Mapping
from datetime import timedelta
from urllib.parse import urlsplit

from django.utils import timezone
from rest_framework import serializers

from .admin_parsers import MAX_SUPPORT_POINT_CONTACTS, MAX_SUPPORT_POINT_ROUTE_LINKS
from .models import ContactChannel, RouteActor
from .support_point_duplicates import reject_support_point_duplicates
from .support_point_normalization import normalized_contact
from .support_point_relations import resolve_support_point_relations

E164_PATTERN = re.compile(r"^\+[1-9][0-9]{7,14}$")


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = sorted(set(data) - set(self.fields))
            if unknown:
                raise serializers.ValidationError(
                    {field: ["Campo não permitido."] for field in unknown},
                    code="unknown_field",
                )
        return super().to_internal_value(data)


class SupportPointActorInputSerializer(StrictSerializer):
    category_id = serializers.UUIDField()
    public_name = serializers.CharField(min_length=1, max_length=160, trim_whitespace=True)
    legal_name = serializers.CharField(
        max_length=200, trim_whitespace=True, required=False, default=""
    )
    short_description = serializers.CharField(
        min_length=1,
        max_length=180,
        trim_whitespace=True,
    )
    full_description = serializers.CharField(
        max_length=10_000,
        trim_whitespace=True,
        required=False,
        default="",
    )
    services = serializers.ListField(
        child=serializers.CharField(min_length=1, max_length=120, trim_whitespace=True),
        max_length=20,
        required=False,
        default=list,
    )

    def validate_services(self, value):
        normalized = [service.strip() for service in value]
        if len({service.casefold() for service in normalized}) != len(normalized):
            raise serializers.ValidationError("Serviços repetidos não são permitidos.")
        return normalized


class SupportPointAddressInputSerializer(StrictSerializer):
    street = serializers.CharField(max_length=160, trim_whitespace=True, required=False)
    number = serializers.CharField(max_length=40, trim_whitespace=True, required=False)
    complement = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    neighborhood = serializers.CharField(max_length=120, trim_whitespace=True, required=False)
    locality = serializers.CharField(min_length=1, max_length=120, trim_whitespace=True)
    administrative_area = serializers.CharField(
        max_length=120, trim_whitespace=True, required=False
    )
    postal_code = serializers.CharField(max_length=20, trim_whitespace=True, required=False)
    country_code = serializers.RegexField(r"^[A-Za-z]{2}$")

    def validate_country_code(self, value):
        return value.upper()


class SupportPointLocationInputSerializer(StrictSerializer):
    label = serializers.CharField(min_length=1, max_length=120, trim_whitespace=True)
    address_fields = SupportPointAddressInputSerializer()
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    public_visibility = serializers.BooleanField()

    def validate(self, attrs):
        if not math.isfinite(attrs["latitude"]) or not math.isfinite(attrs["longitude"]):
            raise serializers.ValidationError("As coordenadas devem ser números finitos.")
        return attrs


class SupportPointContactInputSerializer(StrictSerializer):
    channel_type = serializers.ChoiceField(choices=ContactChannel.ChannelType.choices)
    value = serializers.CharField(
        min_length=1, max_length=500, trim_whitespace=True, write_only=True
    )
    is_public = serializers.BooleanField()
    source_type = serializers.ChoiceField(
        choices=(
            ContactChannel.SourceType.CONSOLIDATED_SHEET,
            ContactChannel.SourceType.TOURISM_INVENTORY,
            ContactChannel.SourceType.OTHER_PUBLIC,
        ),
        required=False,
        default="",
    )
    source_reference = serializers.CharField(
        min_length=1,
        max_length=200,
        trim_whitespace=True,
        required=False,
        default="",
    )
    verified_at = serializers.DateTimeField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        channel_type = attrs["channel_type"]
        value = attrs["value"]
        if not attrs["is_public"]:
            raise serializers.ValidationError(
                {"is_public": ["O cadastro manual aceita somente contatos públicos."]},
                code="private_contact_unsupported",
            )
        if channel_type in {ContactChannel.ChannelType.PHONE, ContactChannel.ChannelType.WHATSAPP}:
            if not E164_PATTERN.fullmatch(value):
                raise serializers.ValidationError({"value": ["Use o formato internacional E.164."]})
        elif channel_type == ContactChannel.ChannelType.EMAIL:
            value = serializers.EmailField(max_length=254).run_validation(value).casefold()
        else:
            value = serializers.URLField(max_length=500).run_validation(value)
            try:
                parsed = urlsplit(value)
                _ = parsed.port
            except ValueError:
                raise serializers.ValidationError({"value": ["URL inválida."]}) from None
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
            ):
                raise serializers.ValidationError(
                    {"value": ["Use uma URL HTTPS pública, sem credenciais embutidas."]}
                )
        attrs["value"] = normalized_contact(channel_type, value)

        public_errors = {}
        if not attrs["source_type"]:
            public_errors["source_type"] = ["Informe o tipo da fonte pública."]
        if not attrs["source_reference"]:
            public_errors["source_reference"] = ["Informe a proveniência do contato público."]
        if attrs["verified_at"] is None:
            public_errors["verified_at"] = ["Informe quando o contato público foi verificado."]
        if public_errors:
            raise serializers.ValidationError(public_errors)
        if attrs["verified_at"] and attrs["verified_at"] > timezone.now() + timedelta(minutes=5):
            raise serializers.ValidationError(
                {"verified_at": ["A verificação não pode estar no futuro."]}
            )
        return attrs


class SupportPointRouteLinkInputSerializer(StrictSerializer):
    route_id = serializers.UUIDField()
    stage_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    route_role = serializers.ChoiceField(choices=RouteActor.RouteRole.choices)
    editorial_position = serializers.IntegerField(min_value=1, max_value=32_767)
    is_featured = serializers.BooleanField()
    sponsorship_label = serializers.CharField(
        max_length=160, trim_whitespace=True, allow_blank=True
    )


class SupportPointCreateRequestSerializer(StrictSerializer):
    actor = SupportPointActorInputSerializer()
    location = SupportPointLocationInputSerializer()
    contacts = SupportPointContactInputSerializer(
        many=True,
        max_length=MAX_SUPPORT_POINT_CONTACTS,
    )
    route_links = SupportPointRouteLinkInputSerializer(
        many=True,
        min_length=1,
        max_length=MAX_SUPPORT_POINT_ROUTE_LINKS,
    )

    resolved_relations = None

    def validate(self, attrs):
        contact_keys = [
            (contact["channel_type"], contact["value"]) for contact in attrs["contacts"]
        ]
        if len(set(contact_keys)) != len(contact_keys):
            raise serializers.ValidationError(
                {"contacts": ["Contatos repetidos não são permitidos."]},
                code="duplicate_input",
            )

        route_keys = [
            (link["route_id"], link.get("stage_id"), link["route_role"])
            for link in attrs["route_links"]
        ]
        if len(set(route_keys)) != len(route_keys):
            raise serializers.ValidationError(
                {"route_links": ["Vínculos repetidos não são permitidos."]},
                code="duplicate_input",
            )

        request = self.context.get("request")
        user = self.context.get("user") or getattr(request, "user", None)
        self.resolved_relations = resolve_support_point_relations(user=user, data=attrs)
        reject_support_point_duplicates(
            region=self.resolved_relations.region,
            public_name=attrs["actor"]["public_name"],
            address_fields=attrs["location"]["address_fields"],
            point=self.resolved_relations.point,
            contacts=attrs["contacts"],
        )
        return attrs
