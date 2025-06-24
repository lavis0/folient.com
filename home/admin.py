from django.contrib import admin
from django import forms
from home.models import Blog
class BlogAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'time']
    list_filter = ['category', 'time']
    search_fields = ['title', 'content']

admin.site.register(Blog, BlogAdmin)
