from django.contrib import admin
from .models import Profile, Student, Teacher
from django.core.mail import send_mail as send_email
# Register your models here.
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_phone', 'is_verified', 'experience_years', 'created_at', 'get_username', 'get_email', 'cv', 'specializations')
    search_fields = ('profile__user__username', 'profile__user__email')
    list_filter = ('is_verified', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('profile', 'cv', 'is_verified', 'experience_years', 'linkedin_url', 'specializations', 'address')
        }),
    )
    actions = ['verify_teacher', 'unverify_teacher', 'custom_delete']

    # Custom display methods
    def get_phone(self, obj):
        return obj.profile.phone
    get_phone.short_description = "Phone"

    def get_username(self, obj):
        return obj.profile.user.username
    get_username.short_description = "Username"

    def get_email(self, obj):
        return obj.profile.user.email
    get_email.short_description = "Email"

    # Custom actions
    def verify_teacher(self, request, queryset):
        for teacher in queryset:
            if not teacher.is_verified:
                teacher.is_verified = True
                teacher.save()
            send_email(
                subject='Account Verification Confirmation',
                message=f'Your account with username {teacher.profile.user.username} has been verified by our admin.',  
                from_email="noreply@gmail.com",
                recipient_list=[teacher.profile.user.email],
                fail_silently=False,
                )
    verify_teacher.short_description = "Verify selected teachers"

    def unverify_teacher(self, request, queryset):
        for teacher in queryset:
            if not teacher.is_verified:
                teacher.is_verified = False
                teacher.save()
            send_email(
                subject='Account Verification Confirmation',
                message=f'Your account with username {teacher.profile.user.username} has been marked temporarily unverified by our admin.',  
                from_email="noreply@gmail.com",
                recipient_list=[teacher.profile.user.email],
                fail_silently=False,
                )        
    unverify_teacher.short_description = "Unverify selected teachers"

    def custom_delete(self, request, queryset):
        for teacher in queryset:
            teacher.delete()
            send_email(
                subject='Account Deletion Confirmation',
                message=f'Your account with username {teacher.profile.user.username} has been deleted.',  
                from_email="noreply@gmail.com",
                recipient_list=[teacher.profile.user.email],
                fail_silently=False,
                )
    custom_delete.short_description = "Delete selected teachers"
