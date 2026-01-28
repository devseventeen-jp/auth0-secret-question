from rest_framework import serializers

class Auth0TokenSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    access_token = serializers.CharField(required=False)

class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    is_approved = serializers.BooleanField()
    has_answered = serializers.BooleanField()
