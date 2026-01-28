from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import User, ApprovalLog


@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "actor", "timestamp")
    readonly_fields = ("user", "actor", "action", "reason", "timestamp")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class ApprovalLogInline(admin.TabularInline):
    model = ApprovalLog
    fk_name = "user"
    extra = 0
    readonly_fields = ("action", "actor", "reason", "timestamp")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

class UserAdminForm(UserChangeForm):
    admin_memo = forms.CharField(
        label="Admin Memo",
        required=False,
        help_text="One-line memo for this approval action (recorded in logs)",
        widget=forms.TextInput(attrs={'style': 'width: 80%;'})
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        is_approved = cleaned_data.get("is_approved")
        rejection_reason = cleaned_data.get("rejection_reason")
        
        # has_answered is readonly so it might not be in cleaned_data
        # but we can check the instance.
        if not is_approved and self.instance.has_answered and not rejection_reason:
            raise forms.ValidationError(
                "Please enter the reason for rejection. (Required if you are disapproving a user who has pending responses)"
            )
        return cleaned_data

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    list_display = (
        "username",
        "email",
        "has_answered",
        "is_approved",
        "is_staff",
        "date_joined",
    )
    list_filter = ("has_answered", "is_approved", "is_staff")
    search_fields = ("username", "email")
    readonly_fields = ("secret_answer", "has_answered", "date_joined", "last_login")

    # fieldsets をカスタマイズして「秘密の質問」セクションを追加
    # password フィールドは変更不可にするか、表示を工夫する
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("email",)}),
        ("Secret Question", {
            "fields": ("secret_answer", "has_answered", "is_approved", "rejection_reason", "admin_memo"),
        }),

        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    inlines = [ApprovalLogInline]

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = User.objects.get(pk=obj.pk)
            memo = form.cleaned_data.get('admin_memo', '')
            
            # Detect approval change
            if not old_obj.is_approved and obj.is_approved:
                reason = "Status marked as approved in adminConsole"
                if memo:
                    reason = f"{reason} | Memo: {memo}"
                
                ApprovalLog.objects.create(
                    user=obj,
                    actor=request.user,
                    action='APPROVED',
                    reason=reason
                )
            # Detect rejection/reason change
            elif old_obj.rejection_reason != obj.rejection_reason and obj.rejection_reason:
                reason = obj.rejection_reason
                if memo:
                    reason = f"{reason} | Memo: {memo}"
                
                # If reason is updated and user is NOT approved, log it as rejection update or new rejection
                ApprovalLog.objects.create(
                    user=obj,
                    actor=request.user,
                    action='REJECTED',
                    reason=reason
                )
            elif old_obj.is_approved and not obj.is_approved:
                 reason = obj.rejection_reason or "Approval revoked"
                 if memo:
                    reason = f"{reason} | Memo: {memo}"

                 ApprovalLog.objects.create(
                    user=obj,
                    actor=request.user,
                    action='REJECTED',
                    reason=reason
                )
            elif memo and not (not old_obj.is_approved and obj.is_approved) and not (old_obj.rejection_reason != obj.rejection_reason):
                # If only memo is provided without status change, log it as a general note or just store it?
                # User specifically asked for memo 'on approval/rejection', 
                # but we can also support manual 'SUBMITTED' (update) if needed.
                # For now, following 'on approval/rejection' specifically.
                pass
        
        super().save_model(request, obj, form, change)

    def has_answer(self, obj):
        return bool(obj.secret_answer)

    has_answer.boolean = True
