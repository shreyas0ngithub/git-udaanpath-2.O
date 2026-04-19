from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, School, Teacher, Parent

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'date_joined')
    search_fields = ('email',)
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_type', 'password1', 'password2'),
        }),
    )

# School Admin
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'school_id', 'principal_name', 'located_at', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('school_name', 'school_id', 'principal_name', 'school_email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'school_id', 'located_at', 'principal_name')
        }),
        ('Contact Details', {
            'fields': ('school_email',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )

# Teacher Admin
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'teacher_id', 'school', 'class_assigned', 'section_assigned', 'is_active', 'created_at')
    list_filter = ('school', 'class_assigned', 'section_assigned', 'is_active', 'created_at')
    search_fields = ('teacher_name', 'teacher_id', 'user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'teacher_name', 'teacher_id', 'mobile_number')
        }),
        ('School Assignment', {
            'fields': ('school', 'class_assigned', 'section_assigned')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )

# Parent Admin
class ParentAdmin(admin.ModelAdmin):
    list_display = ('child_name', 'child_class', 'child_section', 'is_verified', 'school', 'created_at')
    list_filter = ('is_verified', 'child_class', 'child_section', 'school', 'created_at')
    search_fields = ('child_name', 'user__email')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Parent Information', {
            'fields': ('user',)
        }),
        ('Child Information', {
            'fields': ('child_name', 'child_class', 'child_section', 'child_dob')
        }),
        ('Verification', {
            'fields': ('is_verified', 'school')
        }),
        ('Status', {
            'fields': ('created_at',)
        }),
    )
    
    actions = ['verify_parents', 'unverify_parents']
    
    def verify_parents(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} parents were successfully verified.')
    verify_parents.short_description = "Mark selected parents as verified"
    
    def unverify_parents(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} parents were marked as unverified.')
    unverify_parents.short_description = "Mark selected parents as unverified"

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(School, SchoolAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Parent, ParentAdmin)

# Customize admin site
admin.site.site_header = "UdaanPath Administration"
admin.site.site_title = "UdaanPath Admin"
admin.site.index_title = "Welcome to UdaanPath Administration"