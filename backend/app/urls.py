from django.urls import path
from .views import (
    AuthorizeView, 
    MeView, 
    SecretQuestionView,
    MeStatusView,
    ApproveUserView,
)

urlpatterns = [
    path('auth/authorize', AuthorizeView.as_view(), name='authorize'),
    path('auth/me', MeView.as_view(), name='me'),
    path('auth/secret-question', SecretQuestionView.as_view(), name='secret-question'),
    path('auth/status', MeStatusView.as_view(), name='me-status'),
    path('auth/approve/<int:user_id>', ApproveUserView.as_view(), name='approve-user'),
]
