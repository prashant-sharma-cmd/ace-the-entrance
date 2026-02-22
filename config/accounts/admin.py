# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User, EmailVerificationToken, UserOnboarding

class UserOnboardingInline(admin.StackedInline):
    model = UserOnboarding
    can_delete = False
    verbose_name = "Onboarding Profile"
    fields = (
        'primary_purpose',
        'visit_frequency',
        'how_discovered',
        'completed',
        'complete_date', # Fixed: was 'completed_at'
    )
    readonly_fields = ('complete_date',) # Fixed: was 'completed_at'
    extra = 0

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', # Custom users often prioritize email
        'username',
        'is_onboarded',
        'is_staff',
        'is_active',
        'date_joined',
    )
    list_filter = (
        'is_staff',
        'is_active',
        'groups',
        # Removed 'email_verified' because it's not in your model
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    date_hierarchy = 'date_joined'

    # Fixed: Removed 'email_verified' and 'avatar' as they aren't in your User model
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Site-specific', {
            'fields': ('phone_number',),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Site-specific', {
            'fields': ('email', 'phone_number'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login')
    inlines = (UserOnboardingInline,)

    @admin.display(description='Onboarded')
    def is_onboarded(self, obj):
        onboarding = getattr(obj, 'onboarding', None)
        if onboarding and onboarding.completed:
            # Pass color and text as arguments to format_html
            return format_html(
                '<span style="color:#15803d;font-weight:700;">{}</span>',
                "✓ Done")
        return format_html(
            '<span style="color:#92400e;font-weight:700;">{}</span>',
            "− Pending")

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'short_token', 'status_badge', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('token', 'created_at', 'user')

    def has_add_permission(self, request): return False

    @admin.display(description='Email')
    def user_email(self, obj): return obj.user.email

    @admin.display(description='Token (short)')
    def short_token(self, obj):
        return format_html('<code>{}</code>', str(obj.token)[:8] + '...')

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_used: return format_html('<span style="color:gray;">Used</span>')
        if obj.is_expired(): return format_html('<span style="color:red;">Expired</span>')
        return format_html('<span style="color:green;">Active</span>')

@admin.register(UserOnboarding)
class UserOnboardingAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'primary_purpose', 'completed_badge', 'complete_date')
    list_filter = ('completed', 'primary_purpose')
    readonly_fields = ('user', 'complete_date') # Fixed: was 'completed_at'
    date_hierarchy = 'complete_date' # Fixed: was 'completed_at'

    @admin.display(description='Email')
    def user_email(self, obj): return obj.user.email

    @admin.display(description='Completed')
    def completed_badge(self, obj):
        color = "#15803d" if obj.completed else "#92400e"
        text = "✓ Yes" if obj.completed else "− No"
        # Ensure color and text are passed AFTER the string
        return format_html('<span style="color:{};font-weight:700;">{}</span>',
                           color, text)
