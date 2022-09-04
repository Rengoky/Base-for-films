from django.contrib import admin

from .models import Category, Comment, Genre, Review, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'bio',
        'role',
        'email'
    )
    list_filter = ('role',)


@admin.register(Genre)
class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )
    list_filter = ('slug',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )
    list_filter = ('slug',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'text',
        'score',
        'title',
        'pub_date',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'text',
        'review',
        'pub_date',
    )
