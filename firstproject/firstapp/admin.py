from django.contrib import admin
from .models import Profile, Student, Teacher
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
        queryset.update(is_verified=True)
    verify_teacher.short_description = "Verify selected teachers"

    def unverify_teacher(self, request, queryset):
        queryset.update(is_verified=False)
    unverify_teacher.short_description = "Unverify selected teachers"

    def custom_delete(self, request, queryset):
        for teacher in queryset:
            teacher.delete()
    custom_delete.short_description = "Delete selected teachers"
