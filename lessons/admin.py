from django.contrib import admin
from .models import Lesson, LessonCategory, LessonProgress

@admin.register(LessonCategory)
class LessonCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'upload_date', 'is_active', 'is_featured')
    list_filter = ('category', 'difficulty', 'is_active', 'is_featured')
    search_fields = ('title', 'description', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('upload_date', 'last_updated', 'view_count')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'content')
        }),
        ('Media', {
            'fields': ('file', 'thumbnail')
        }),
        ('Metadata', {
            'fields': ('category', 'difficulty', 'uploaded_by')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('upload_date', 'last_updated', 'view_count'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.uploaded_by_id:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'completed', 'last_viewed')
    list_filter = ('completed', 'last_viewed')
    search_fields = ('user__username', 'lesson__title')
    readonly_fields = ('last_viewed',)