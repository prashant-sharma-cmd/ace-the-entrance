from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    User,
    UserOnboarding,
    EmailVerificationToken,
    DeletionOTP,
    PasswordResetToken,
)


# ── Inlines ───────────────────────────────────────────────────────────────────

class UserOnboardingInline(admin.StackedInline):
    model         = UserOnboarding
    can_delete    = False
    verbose_name  = "Onboarding Profile"
    fields        = (
        'primary_purpose',
        'visit_frequency',
        'how_discovered',
        'newsletter_opt_in',
        'completed',
        'complete_date',
    )
    readonly_fields = ('complete_date',)
    extra = 0


# ── User ──────────────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email',
        'username',
        'full_name',
        'phone_number',
        'email_verified_badge',
        'is_onboarded',
        'is_active',
        'is_staff',
        'date_joined',
    )
    list_filter  = ('is_staff', 'is_active', 'email_verified', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering      = ('-date_joined',)
    date_hierarchy = 'date_joined'
    readonly_fields = ('date_joined', 'last_login')
    inlines = (UserOnboardingInline,)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Contact & Verification', {
            'fields': ('phone_number', 'email_verified'),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Contact & Verification', {
            'fields': ('email', 'phone_number', 'email_verified'),
        }),
    )

    # ── Custom columns ────────────────────────────────────────────────────────

    @admin.display(description='Name')
    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or '—'

    @admin.display(description='Email Verified', boolean=False)
    def email_verified_badge(self, obj):
        if obj.email_verified:
            return format_html(
                '<span style="color:{};font-weight:700;">{}</span>',
                '#15803d', '✓ Verified'
            )
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            '#b91c1c', '✗ Unverified'
        )

    @admin.display(description='Onboarded')
    def is_onboarded(self, obj):
        onboarding = getattr(obj, 'onboarding', None)
        if onboarding and onboarding.completed:
            return format_html(
                '<span style="color:{};font-weight:700;">{}</span>',
                '#15803d', '✓ Done'
            )
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            '#92400e', '− Pending'
        )

    # ── Admin actions ─────────────────────────────────────────────────────────

    actions = ['mark_email_verified', 'mark_email_unverified', 'activate_users', 'deactivate_users']

    @admin.action(description='Mark selected users as email verified')
    def mark_email_verified(self, request, queryset):
        updated = queryset.update(email_verified=True, is_active=True)
        self.message_user(request, f"{updated} user(s) marked as verified and activated.")

    @admin.action(description='Mark selected users as email unverified')
    def mark_email_unverified(self, request, queryset):
        updated = queryset.update(email_verified=False, is_active=False)
        self.message_user(request, f"{updated} user(s) marked as unverified and deactivated.")

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} user(s) activated.")

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        # Prevent deactivating yourself
        updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"{updated} user(s) deactivated.")


# ── UserOnboarding ────────────────────────────────────────────────────────────

@admin.register(UserOnboarding)
class UserOnboardingAdmin(admin.ModelAdmin):
    list_display  = (
        'user',
        'user_email',
        'primary_purpose',
        'visit_frequency',
        'how_discovered',
        'newsletter_opt_in',
        'completed_badge',
        'complete_date',
    )
    list_filter   = ('completed', 'primary_purpose', 'visit_frequency', 'newsletter_opt_in')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'complete_date')
    date_hierarchy  = 'complete_date'

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Completed')
    def completed_badge(self, obj):
        if obj.completed:
            return format_html(
                '<span style="color:{};font-weight:700;">{}</span>',
                '#15803d', '✓ Yes'
            )
        return format_html(
            '<span style="color:{};font-weight:700;">{}</span>',
            '#92400e', '− No'
        )


# ── EmailVerificationToken ────────────────────────────────────────────────────

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display  = ('user', 'user_email', 'short_token', 'status_badge', 'created_at', 'is_used')
    list_filter   = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'user')
    ordering      = ('-created_at',)

    def has_add_permission(self, request):
        return False

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Token (short)')
    def short_token(self, obj):
        return format_html('<code>{}</code>', str(obj.token)[:8] + '…')

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color:{};">Used</span>', '#6b7280')
        if obj.is_expired():
            return format_html('<span style="color:{};font-weight:600;">Expired</span>', '#b91c1c')
        return format_html('<span style="color:{};font-weight:600;">Active</span>', '#15803d')

    actions = ['revoke_tokens']

    @admin.action(description='Revoke selected tokens')
    def revoke_tokens(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f"{updated} token(s) revoked.")


# ── DeletionOTP ───────────────────────────────────────────────────────────────

@admin.register(DeletionOTP)
class DeletionOTPAdmin(admin.ModelAdmin):
    list_display  = (
        'user',
        'user_email',
        'short_code',
        'attempt_count',
        'status_badge',
        'created_at',
        'is_used',
    )
    list_filter   = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('user', 'code', 'created_at', 'attempt_count')
    ordering      = ('-created_at',)

    # OTP codes should never be manually created via admin
    def has_add_permission(self, request):
        return False

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Code')
    def short_code(self, obj):
        # Show only first 2 digits in admin for audit — full code not needed
        return format_html('<code>{}****</code>', obj.code[:2])

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color:{};">Used</span>', '#6b7280')
        if obj.is_locked():
            return format_html(
                '<span style="color:{};font-weight:600;">Locked ({} attempts)</span>',
                '#b91c1c', obj.attempt_count
            )
        if obj.is_expired():
            return format_html('<span style="color:{};font-weight:600;">Expired</span>', '#b91c1c')
        remaining = obj.MAX_ATTEMPTS - obj.attempt_count
        return format_html(
            '<span style="color:{};font-weight:600;">Active ({} attempt(s) left)</span>',
            '#15803d', remaining
        )

    actions = ['revoke_otps']

    @admin.action(description='Revoke selected OTPs')
    def revoke_otps(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f"{updated} OTP(s) revoked.")


# ── PasswordResetToken ────────────────────────────────────────────────────────

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display  = ('user', 'user_email', 'short_token', 'status_badge', 'created_at', 'is_used')
    list_filter   = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'user')
    ordering      = ('-created_at',)

    def has_add_permission(self, request):
        return False

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Token (short)')
    def short_token(self, obj):
        return format_html('<code>{}</code>', str(obj.token)[:8] + '…')

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_used:
            return format_html('<span style="color:{};">Used</span>', '#6b7280')
        if obj.is_expired():
            return format_html('<span style="color:{};font-weight:600;">Expired</span>', '#b91c1c')
        from datetime import timedelta
        expires_at = obj.created_at + timedelta(hours=1)
        remaining  = expires_at - timezone.now()
        mins       = max(0, int(remaining.total_seconds() // 60))
        return format_html(
            '<span style="color:{};font-weight:600;">Active (~{}m left)</span>',
            '#15803d', mins
        )

    actions = ['revoke_tokens']

    @admin.action(description='Revoke selected tokens')
    def revoke_tokens(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f"{updated} token(s) revoked.")