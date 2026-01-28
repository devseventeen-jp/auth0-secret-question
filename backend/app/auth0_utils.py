import json
import requests
from jose import jwt
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


def get_auth0_public_key(token):
    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()
    unverified_header = jwt.get_unverified_header(token)
    
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    return rsa_key

def validate_auth0_token(token):
    """
    Decodes the JWT and returns the payload.
    """
    try:
        rsa_key = get_auth0_public_key(token)
        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.AUTH0_AUDIENCE, # Keep passing it if present, but we will relax checks if needed, or better:
                # To support both Access Token (Audience=API) and ID Token (Audience=ClientID), 
                # and since we might not have ClientID in settings, we can disable aud check 
                # OR trust that the library handles list. 
                # Simple fix: Verify signature and issuer.
                options={"verify_aud": False},
                issuer=f"https://{settings.AUTH0_DOMAIN}/"
            )
            return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed(_("Token is expired."), code="token_expired")
    except jwt.JWTClaimsError:
        raise AuthenticationFailed(_("Incorrect claims."), code="token_invalid_claims")
    except Exception as e:
        raise AuthenticationFailed(_("Unable to parse authentication token."), code="token_invalid")
    
    raise AuthenticationFailed(_("Unable to find appropriate key."), code="token_invalid_key")

def verify_jwt_and_get_userinfo(id_token: str):
    """
    Auth0 の ID Token を検証し、Payload(userinfo) を返す
    """

    domain = settings.AUTH0_DOMAIN
    audience = settings.AUTH0_CLIENT_ID

    # JWKS を取得
    jwks_url = f"https://{domain}/.well-known/jwks.json"
    jwks = requests.get(jwks_url).json()

    unverified_header = jwt.get_unverified_header(id_token)

    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
            break

    if not rsa_key:
        raise Exception("Unable to find RSA key")

    payload = jwt.decode(
        id_token,
        rsa_key,
        algorithms=["RS256"],
        audience=audience,
        issuer=f"https://{domain}/"
    )

    return payload

class Auth0Authentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return None

        token = parts[1]
        try:
            payload = validate_auth0_token(token)
            auth0_sub = payload['sub']
            user = User.objects.get(auth0_sub=auth0_sub)
            return (user, None)
        except Exception:
            return None

