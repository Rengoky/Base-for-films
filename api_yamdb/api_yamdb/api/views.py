import random

from api.serializers import (CategorySerializer, CheckCodeSerializer,
                             GenreSerializer, TitleSerializer, UserSerializer,
                             UsersMeSerializer)
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import ParseError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from reviews.models import Category, Genre, Review, Title, User

from api_yamdb.settings import TEST_EMAIL

from .filters import TitleFilter
from .mixins import ListCreateDestroyViewSet
from .permissions import (IsAdmin, IsAdminModeratorOwnerOrReadOnly,
                          IsAdminOrReadOnly)
from .serializers import CommentSerializer, ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminModeratorOwnerOrReadOnly]

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        return title.reviews.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        if Review.objects.filter(title=title,
                                 author=self.request.user).exists():
            raise ParseError('Вы уже написали ревью к этому произведению')
        serializer.save(author=self.request.user, title=title)
        rating = Review.objects.filter(title=title).aggregate(Avg('score'))
        title.rating = rating['score__avg']
        title.save(update_fields=['rating'])

    def perform_update(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, pk=title_id)
        serializer.save(author=self.request.user, title=title)
        rating = Review.objects.filter(title=title).aggregate(Avg('score'))
        title.rating = rating['score__avg']
        title.save(update_fields=['rating'])


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAdminModeratorOwnerOrReadOnly]

    def get_queryset(self):
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id)
        return review.comments.all()

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, id=review_id, title=title_id)
        serializer.save(author=self.request.user, review=review)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    serializer_class = TitleSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAdminOrReadOnly,)
    filterset_class = TitleFilter

    def perform_create(self, serializer):
        category = Category.objects.get(
            slug=self.request.data.get('category')
        )
        genre = Genre.objects.filter(
            slug__in=self.request.data.getlist('genre')
        )
        serializer.save(category=category, genre=genre)


class CategoryViewSet(ListCreateDestroyViewSet):
    queryset = Category.objects.all()
    lookup_field = ('slug')
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class GenreViewSet(ListCreateDestroyViewSet):
    queryset = Genre.objects.all()
    lookup_field = ('slug')
    serializer_class = GenreSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


@api_view(['POST'])
def send_code(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.data.get('username')
        email = serializer.data.get('email')
        confirmation_code = ''.join(map(str, random.sample(range(10), 5)))
        User.objects.get_or_create(
            username=username,
            email=email,
            confirmation_code=make_password(
                confirmation_code,
                salt=None,
                hasher='default'
            )
        )
        send_mail(
            'Код подтверждения',
            confirmation_code,
            TEST_EMAIL,
            [email],
            fail_silently=False
        )
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def get_token(request):
    serializer = CheckCodeSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.data.get('username')
        confirmation_code = serializer.data.get('confirmation_code')
        user = get_object_or_404(User, username=username)
        if check_password(confirmation_code, user.confirmation_code):
            token = AccessToken.for_user(user)
            return Response({'token': token}, status=status.HTTP_200_OK)
        return Response({'confirmation_code': 'Неверный код подтверждения!'},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'
    permission_classes = (IsAdmin,)
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    pagination_class = LimitOffsetPagination

    @action(
        methods=['get', 'patch'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def users_me(self, request):
        if request.method == 'GET':
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        serializer = UsersMeSerializer(request.user, request.data,
                                       partial=True)
        if request.user.role == 'admin':
            serializer = UserSerializer(request.user, request.data,
                                        partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
