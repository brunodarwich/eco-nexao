from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)


class AdminIdentitySerializer(serializers.Serializer):
    id = serializers.CharField()
    username = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField())
    actions = serializers.ListField(child=serializers.CharField())
    region_slugs = serializers.ListField(child=serializers.SlugField())


class SessionResponseSerializer(serializers.Serializer):
    authenticated = serializers.BooleanField()
    user = AdminIdentitySerializer(allow_null=True)


class CsrfResponseSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()
