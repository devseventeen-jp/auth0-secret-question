from rest_framework import serializers

class Auth0TokenSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    access_token = serializers.CharField(required=False)

class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    real_name = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    is_approved = serializers.BooleanField()
    has_answered = serializers.BooleanField()
