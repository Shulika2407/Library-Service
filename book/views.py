from django.shortcuts import render

# Create your views here.
from book.serializers import BookSerializer
from book.models import Book
from rest_framework import viewsets
from book.permissions import IsAdminUserForWriteElseReadOnly


class BookViews(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    permission_classes = (IsAdminUserForWriteElseReadOnly,)
