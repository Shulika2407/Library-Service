from django.contrib import admin
from django.core.checks import register

from .models import Book

# Register your models here.


admin.site.register(Book)
