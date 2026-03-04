from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import AuthenticationFailed
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from urllib.parse import urlparse
from .models import User, ApprovalLog

from .serializers import Auth0TokenSerializer, UserSerializer
from .auth0_utils import (
    validate_auth0_token,
    verify_jwt_and_get_userinfo,
    generate_internal_jwt_token,
    verify_internal_jwt_token,
    decode_internal_jwt_token_allow_expired,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _resolve_user_from_id_token(id_token):
    userinfo = verify_jwt_and_get_userinfo(id_token)
    auth0_sub = userinfo["sub"]
    nickname = userinfo.get("nickname")
    email = userinfo.get("email")
    if not email:
        raise ValueError("email claim is missing")

    suggested_username = nickname or email.split('@')[0] or auth0_sub

    user, created = User.objects.get_or_create(
        auth0_sub=auth0_sub,
        defaults={
            "username": suggested_username,
            "email": email,
        },
    )
    if created:
        user.set_unusable_password()
        user.save()
    elif user.email != email:
        user.email = email
        user.save(update_fields=["email"])

    logger.info(
        "resolve_user_from_id_token sub=%s email=%s user_id=%s created=%s",
        auth0_sub,
        email,
        user.id,
        created,
    )

    return user


def _is_allowed_return_to(return_to):
    if not return_to:
        return False

    parsed = urlparse(return_to)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False

    target_origin = f"{parsed.scheme}://{parsed.netloc}"
    return target_origin in settings.RETURN_TO_ALLOWLIST

class AuthorizeView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"message": "No token"}, status=400)

        try:
            user = _resolve_user_from_id_token(token)
        except Exception:
            return Response({"message": "Invalid token"}, status=401)

        if not user.has_answered:
            return Response({"status": "needs_secret"}, status=200)

        if not user.is_approved:
            return Response({"status": "needs_approval"}, status=200)

        return Response({"status": "ok"}, status=200)


class CallbackSessionView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request):
        id_token = request.data.get("id_token")
        return_to = request.data.get("return_to")

        if not id_token:
            return Response({"message": "No token"}, status=400)

        if return_to and not _is_allowed_return_to(return_to):
            return Response({"message": "Invalid return_to"}, status=400)

        try:
            user = _resolve_user_from_id_token(id_token)
        except Exception:
            return Response({"message": "Invalid token"}, status=401)

        logger.info(
            "session/callback state user_id=%s has_answered=%s is_approved=%s return_to=%s",
            user.id,
            user.has_answered,
            user.is_approved,
            bool(return_to),
        )

        if not user.has_answered:
            return Response({"status": "needs_secret"}, status=200)

        if not user.is_approved:
            return Response({"status": "needs_approval"}, status=200)

        token = generate_internal_jwt_token(user, expires_in_hours=24)
        response = Response({
            "status": "ok",
            "return_to": return_to,
        }, status=200)
        response.set_cookie(
            key=settings.INTERNAL_JWT_COOKIE_NAME,
            value=token,
            max_age=settings.INTERNAL_JWT_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.INTERNAL_JWT_COOKIE_SECURE,
            samesite=settings.INTERNAL_JWT_COOKIE_SAMESITE,
            path=settings.INTERNAL_JWT_COOKIE_PATH,
            domain=settings.INTERNAL_JWT_COOKIE_DOMAIN,
        )
        return response


class ValidateCookieSessionView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        cookie_name = settings.INTERNAL_JWT_COOKIE_NAME
        token = request.COOKIES.get(cookie_name)
        if not token:
            return Response(
                {"valid": False, "detail": f"Cookie '{cookie_name}' is missing"},
                status=401
            )

        try:
            payload = verify_internal_jwt_token(token)
            return Response({
                "valid": True,
                "user_id": payload["user_id"],
                "username": payload["username"],
                "email": payload["email"],
                "is_approved": payload["is_approved"],
                "has_answered": payload["has_answered"],
            }, status=200)
        except Exception as e:
            return Response({"valid": False, "detail": str(e)}, status=401)


class ClaimsCookieSessionView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def get(self, request):
        cookie_name = settings.INTERNAL_JWT_COOKIE_NAME
        token = request.COOKIES.get(cookie_name)
        if not token:
            return Response(
                {"message": f"Cookie '{cookie_name}' is missing"},
                status=401
            )

        try:
            payload = verify_internal_jwt_token(token)
        except Exception as e:
            return Response({"message": str(e)}, status=401)

        sub = payload.get("auth0_sub")
        email = payload.get("email")

        # Backward compatibility for older tokens that may miss claims.
        if (not sub or not email) and payload.get("user_id"):
            user = User.objects.filter(id=payload["user_id"]).first()
            if user:
                sub = sub or user.auth0_sub
                email = email or user.email

        return Response({
            "sub": sub,
            "email": email,
        }, status=200)


class RefreshCookieSessionView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request):
        cookie_name = settings.INTERNAL_JWT_COOKIE_NAME
        raw_token = request.COOKIES.get(cookie_name)
        if not raw_token:
            return Response(
                {"message": f"Cookie '{cookie_name}' is missing"},
                status=401
            )

        try:
            payload = verify_internal_jwt_token(raw_token)
        except AuthenticationFailed as exc:
            if getattr(exc, "code", "") != "token_expired":
                return Response({"message": "Invalid token"}, status=401)
            try:
                payload = decode_internal_jwt_token_allow_expired(raw_token)
            except AuthenticationFailed:
                return Response({"message": "Invalid token"}, status=401)

        user_id = payload.get("user_id")
        if not user_id:
            return Response({"message": "Invalid token payload"}, status=401)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"message": "User not found"}, status=401)

        logger.info(
            "session/refresh state user_id=%s has_answered=%s is_approved=%s",
            user.id,
            user.has_answered,
            user.is_approved,
        )

        if not user.has_answered:
            return Response({"status": "needs_secret"}, status=200)

        if not user.is_approved:
            return Response({"status": "needs_approval"}, status=200)

        token = generate_internal_jwt_token(user, expires_in_hours=24)
        response = Response({"status": "ok"}, status=200)
        response.set_cookie(
            key=settings.INTERNAL_JWT_COOKIE_NAME,
            value=token,
            max_age=settings.INTERNAL_JWT_COOKIE_MAX_AGE,
            httponly=True,
            secure=settings.INTERNAL_JWT_COOKIE_SECURE,
            samesite=settings.INTERNAL_JWT_COOKIE_SAMESITE,
            path=settings.INTERNAL_JWT_COOKIE_PATH,
            domain=settings.INTERNAL_JWT_COOKIE_DOMAIN,
        )
        return response


class LogoutCookieSessionView(APIView):
    authentication_classes = []
    permission_classes = (AllowAny,)

    def post(self, request):
        response = Response({"status": "ok"}, status=200)
        response.delete_cookie(
            key=settings.INTERNAL_JWT_COOKIE_NAME,
            path=settings.INTERNAL_JWT_COOKIE_PATH,
            domain=settings.INTERNAL_JWT_COOKIE_DOMAIN,
            samesite=settings.INTERNAL_JWT_COOKIE_SAMESITE,
        )
        return response


class MeView(APIView):
    def get(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
             return Response({'error': 'Bearer token required'}, status=401)
        
        token = auth_header.split(' ')[1]
        try:
            payload = validate_auth0_token(token)
            user = User.objects.get(auth0_sub=payload['sub'])
            return Response(UserSerializer(user).data)
        except Exception:
             return Response({'error': 'Invalid token'}, status=401)

class SecretQuestionView(APIView):
    permission_classes = [IsAuthenticated]

    """
    Get status, and retrieve answer.
    """
    def get(self, request):
        user = request.user

        return Response({
            "question": settings.SECRET_QUESTION_TEXT,
            "has_answered": user.has_answered,
            "secret_answer": user.secret_answer,
            "is_approved": user.is_approved,
            "rejection_reason": user.rejection_reason,
        })


    """
    Post answer.
    """
    def post(self, request):
        user = request.user

        if user.is_approved:
            return Response(
                {"detail": "Already approved"},
                status=400
            )

        answer = request.data.get("answer")
        if not answer:
            return Response(
                {"detail": "answer is required"},
                status=400
            )

        user.secret_answer = answer
        user.rejection_reason = None
        user.has_answered = True
        user.save(update_fields=["secret_answer", "rejection_reason", "has_answered"])

        # Log submission
        ApprovalLog.objects.create(
            user=user,
            actor=user,
            action='SUBMITTED',
            reason=f"Answer length: {len(answer)} chars"
        )

        return Response({"status": "submitted"})


class MeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "is_approved": user.is_approved,
            "has_answered": user.has_answered,
        })

class ApproveUserView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        user.is_approved = True
        user.save(update_fields=["is_approved"])

        # Log approval
        ApprovalLog.objects.create(
            user=user,
            actor=request.user,
            action='APPROVED',
            reason="Approved via API"
        )

        return Response({"status": "approved"})

class InternalTokenView(APIView):
    """
    Generate a JWT token for inter-container authentication.
    Can be accessed by authenticated users (Auth0 or other methods).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Generate and return a JWT token for the authenticated user.
        This token can be used to authenticate requests to other containers.
        """
        user = request.user
        expires_in = request.data.get('expires_in_hours', 24)
        
        try:
            token = generate_internal_jwt_token(user, expires_in_hours=int(expires_in))
            return Response({
                'token': token,
                'user_id': user.id,
                'username': user.username,
                'expires_in': expires_in
            }, status=200)
        except Exception as e:
            return Response(
                {"detail": f"Failed to generate token: {str(e)}"},
                status=500
            )


class ValidateInternalTokenView(APIView):
    """
    Validate an internal JWT token and return user information.
    Useful for other containers to verify tokens issued by this service.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validate a JWT token and return the associated user information.
        """
        token = request.data.get('token')
        
        if not token:
            return Response(
                {"detail": "Token is required"},
                status=400
            )
        
        try:
            payload = verify_internal_jwt_token(token)
            return Response({
                'valid': True,
                'user_id': payload['user_id'],
                'username': payload['username'],
                'email': payload['email'],
                'is_approved': payload['is_approved'],
                'has_answered': payload['has_answered'],
            }, status=200)
        except Exception as e:
            return Response({
                'valid': False,
                'detail': str(e)
            }, status=401)
