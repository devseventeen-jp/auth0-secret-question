from django.urls import path
from .views import (
    InternalTokenView,
    ValidateInternalTokenView,
    CallbackSessionView,
    ValidateCookieSessionView,
    ClaimsCookieSessionView,
    RefreshCookieSessionView,
    LogoutCookieSessionView,
)

urlpatterns = [
    path('token', InternalTokenView.as_view(), name='internal-token'),
    path('token/validate', ValidateInternalTokenView.as_view(), name='validate-token'),
    path('session/callback', CallbackSessionView.as_view(), name='callback-session'),
    path('session/validate', ValidateCookieSessionView.as_view(), name='validate-cookie-session'),
    path('claims', ClaimsCookieSessionView.as_view(), name='claims-cookie-session'),
    path('session/refresh', RefreshCookieSessionView.as_view(), name='refresh-cookie-session'),
    path('session/logout', LogoutCookieSessionView.as_view(), name='logout-cookie-session'),
]
