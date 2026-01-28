from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.permissions import IsAdminUser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from .models import User, ApprovalLog

import qrcode
import io
import base64

from .serializers import Auth0TokenSerializer, UserSerializer
from .auth0_utils import validate_auth0_token, verify_jwt_and_get_userinfo

User = get_user_model()

class AuthorizeView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        token = request.data.get("id_token")
        if not token:
            return Response({"message": "No token"}, status=400)

        try:
            userinfo = verify_jwt_and_get_userinfo(token)
        except Exception:
            return Response({"message": "Invalid token"}, status=401)

        auth0_sub = userinfo["sub"]
        nickname = userinfo.get("nickname")
        email = userinfo.get("email")
        
        # Determine a human-readable username
        suggested_username = nickname or (email.split('@')[0] if email else auth0_sub)

        user, created = User.objects.get_or_create(
            auth0_sub=auth0_sub,
            defaults={"username": suggested_username}
        )
        if created:
            user.set_unusable_password()
            user.save()
        if not user.has_answered:
            return Response({"status": "needs_secret"}, status=200)

        if not user.is_approved:
            return Response({"status": "needs_approval"}, status=200)

        return Response({"status": "ok"}, status=200)

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
            "has_answered": bool(user.secret_answer),
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
