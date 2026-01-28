from django.urls import path
from .views import AuthorizeView, MeView, SecretQuestionView

urlpatterns = [
    path('auth/authorize', AuthorizeView.as_view(), name='authorize'),
    path('auth/me', MeView.as_view(), name='me'),
    path('auth/secret-question', SecretQuestionView.as_view(), name='secret-question'),
]
