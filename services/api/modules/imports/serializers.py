from rest_framework import serializers


class CatalogCsvValidationRequestSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False)

    def validate_file(self, value):
        if not value.name.lower().endswith(".csv"):
            raise serializers.ValidationError("Envie um arquivo com extensão .csv.")
        accepted_types = {
            "",
            "application/csv",
            "application/octet-stream",
            "text/csv",
            "text/plain",
            "application/vnd.ms-excel",
        }
        if getattr(value, "content_type", "") not in accepted_types:
            raise serializers.ValidationError("O tipo do arquivo não é compatível com CSV.")
        return value


class CatalogCsvCommitRequestSerializer(CatalogCsvValidationRequestSerializer):
    sha256 = serializers.RegexField(r"^[0-9a-f]{64}$")
    idempotency_key = serializers.UUIDField()
    confirmed = serializers.BooleanField()

    def validate_confirmed(self, value):
        if value is not True:
            raise serializers.ValidationError("Confirme explicitamente a aplicação do lote.")
        return value


class CatalogCsvIssueSerializer(serializers.Serializer):
    severity = serializers.ChoiceField(choices=("error", "warning"))
    code = serializers.CharField()
    line = serializers.IntegerField(min_value=0)
    column = serializers.CharField(allow_null=True)
    message = serializers.CharField()


class CatalogCsvPreviewRowSerializer(serializers.Serializer):
    line = serializers.IntegerField(min_value=2)
    external_id = serializers.CharField()
    operation = serializers.ChoiceField(choices=("create", "update", "archive"))


class CatalogCsvPreviewSerializer(serializers.Serializer):
    create_count = serializers.IntegerField(min_value=0)
    update_count = serializers.IntegerField(min_value=0)
    archive_count = serializers.IntegerField(min_value=0)
    rows = CatalogCsvPreviewRowSerializer(many=True)


class CatalogCsvValidationResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    sha256 = serializers.RegexField(r"^[0-9a-f]{64}$")
    row_count = serializers.IntegerField(min_value=0)
    error_count = serializers.IntegerField(min_value=0)
    warning_count = serializers.IntegerField(min_value=0)
    issues_truncated = serializers.BooleanField()
    issues = CatalogCsvIssueSerializer(many=True)
    preview = CatalogCsvPreviewSerializer(allow_null=True)


class CatalogImportCommitResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=("committed",))
    replayed = serializers.BooleanField()
    sha256 = serializers.RegexField(r"^[0-9a-f]{64}$")
    row_count = serializers.IntegerField(min_value=0)
    warning_count = serializers.IntegerField(min_value=0)
    create_count = serializers.IntegerField(min_value=0)
    update_count = serializers.IntegerField(min_value=0)
    archive_count = serializers.IntegerField(min_value=0)
    committed_at = serializers.DateTimeField()


class CatalogImportCommitErrorSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    field_errors = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()),
    )
    request_id = serializers.UUIDField()
