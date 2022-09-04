from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ADMIN = 'admin'
    MODERATOR = 'moderator'
    USER = 'user'
    ROLES = [
        (ADMIN, 'Administrator'),
        (MODERATOR, 'Moderator'),
        (USER, 'User'),
    ]

    bio = models.TextField(
        verbose_name='Биография',
        blank=True,
    )
    role = models.CharField(
        max_length=9,
        choices=ROLES,
        verbose_name='Роль',
        default='user'
    )
    email = models.EmailField(('Адрес e-mail'), unique=True)
    confirmation_code = models.CharField(max_length=5, default='00000')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        return self.role == self.ADMIN


class Genre(models.Model):
    name = models.CharField(
        verbose_name='Наименование',
        max_length=50
    )
    slug = models.SlugField(unique=True, default='')

    class Meta:
        db_table = 'genre'
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Category(models.Model):
    name = models.CharField(
        verbose_name='Наименование',
        max_length=50
    )
    slug = models.SlugField(unique=True, default='')

    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Title(models.Model):
    name = models.CharField(
        verbose_name='Наименование',
        max_length=100
    )
    description = models.CharField(
        max_length=200,
        null=True
    )
    year = models.PositiveSmallIntegerField(
        verbose_name='Год выпуска'
    )
    date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    genre = models.ManyToManyField(
        Genre,
        blank=True,
        related_name='titles',
    )
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    rating = models.IntegerField(
        verbose_name='Рейтинг',
        null=True,
        default=None
    )

    class Meta:
        db_table = 'title'
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'


class Review(models.Model):
    text = models.TextField()
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews')
    score = models.PositiveSmallIntegerField()
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='reviews')
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('title', 'author'),
                name='unique_review'
            ),
        ]


class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='comments')
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comments')
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
