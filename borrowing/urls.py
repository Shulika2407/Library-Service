from django.urls import path, include
from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns

from borrowing.views import (
    BorrowingViews,
    BorrowingReturnView,
    generate_telegram_link,
    telegram_webhook,
    api_root,
)


app_name = "borrowing"

router = routers.DefaultRouter()
router.register("borrowing", BorrowingViews, basename="borrowing")

urlpatterns = [
    path("", api_root),
    path(
        "borrowing/<int:pk>/return_book/",
        BorrowingReturnView.as_view(),
        name="return_book",
    ),
    path("", include(router.urls)),
    path("generate_telegram_link/", generate_telegram_link, name="generate_link"),
    path("telegram_webhook/", telegram_webhook, name="telegram_webhook"),
]
