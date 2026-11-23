from django.contrib import admin

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)

class RequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'category', 'created_at', 'updated_at', 'status')
    search_fields = ('title', 'description', 'status__name', 'category__name')
    list_filter = ('status',)

class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)
