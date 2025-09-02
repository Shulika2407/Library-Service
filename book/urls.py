from django.urls import path, include
from rest_framework import routers
from book.views import BookViews

app_name = "books"

router = routers.DefaultRouter()
router.register("books", BookViews, basename="books")

urlpatterns = [
    path("", include(router.urls)),
]
