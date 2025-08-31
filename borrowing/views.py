import os
from datetime import date
from enum import unique
from http.client import responses
from django.shortcuts import render
from rest_framework.reverse import reverse
from rest_framework.response import Response


from borrowing.serializers import (
    BorrowingCreateSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, mixins, status, request, views
from rest_framework import generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from borrowing.permissions import IsOwnerOrAdmin
from .models import Borrowing
import requests
from django.contrib.auth import get_user_model
from dotenv import load_dotenv
from library_service import settings
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
load_dotenv()


def send_telegram_message(chat_id: str, message: str):
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        # Возвращаем статус, чтобы было понятно, отправлено сообщение или нет.
        return f"Message sent successfully to chat_id {chat_id}."
    except requests.exceptions.RequestException as e:
        # Возвращаем конкретную ошибку
        return f"Error sending Telegram message to chat_id {chat_id}: {e}"


@api_view(["GET"])
def api_root(request, format=None):
    """
    Кореневе представлення API для додатка Borrowing.
    Відображає посилання на всі доступні ендпоінти.
    """
    return Response(
        {
            "borrowings": reverse(
                "borrowing:borrowing-list", request=request, format=format
            ),
            "generate_telegram_link": reverse(
                "borrowing:generate_link", request=request, format=format
            ),
            "telegram_webhook": reverse(
                "borrowing:telegram_webhook", request=request, format=format
            ),
        }
    )


class BorrowingViews(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    permission_classes = (IsAuthenticated,)
    queryset = Borrowing.objects.prefetch_related("user", "book").order_by("id")

    def get_queryset(self):
        queryset = self.queryset

        if self.request.user.is_staff:
            user_id = self.request.query_params.get("user")
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        else:

            queryset = queryset.filter(user=self.request.user)

        is_active = self.request.query_params.get("is_active")

        if is_active:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            else:

                queryset = queryset.filter(actual_return_date__isnull=False)
        return queryset.distinct()

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)

        if instance.user.telegram_chat_id:
            personal_message = (
                f"<b>Hello, {instance.user.full_name}!</b>\n "
                f"You have downloaded the book <b>{instance.book.title}</b>."
                f" Enjoy reading!"
            )
            send_telegram_message(
                chat_id=instance.user.telegram_chat_id, message=personal_message
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "user_id",
                type=int,
                description="Filter by user_id (ex ?user_id=1)",
                required=False,
            ),
            OpenApiParameter(
                "is_active", type=bool, description="Filter by is_active user"
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "create":
            return BorrowingCreateSerializer
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingListSerializer


class BorrowingReturnView(views.APIView):
    permission_classes = (
        IsAuthenticated,
        IsOwnerOrAdmin,
    )

    def get(self, request, pk):
        return Response({"message": f"The book with ID {pk} will be returned"})

    def post(self, request, pk=None):
        try:
            borrowing = Borrowing.objects.get(pk=pk)
        except Borrowing.DoesNotExist:
            return Response(
                {"error": "Loan record not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if borrowing.actual_return_date:
            return Response(
                {"error": "The book has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = date.today()
        borrowing.save()

        book = borrowing.book
        book.inventory += 1
        book.save()
        return Response(
            {"message": "The book has been successfully returned!", "book_id": book.id},
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_telegram_link(request):
    user = request.user
    unique_token = "some-unique-token-for-user-" + str(user.id)

    bot_username = settings.TELEGRAM_BOT_USERNAME
    telegram_url = f"https://t.me/{bot_username}?start={unique_token}"

    return Response({"telegram_link": telegram_url})


@api_view(["POST"])
@permission_classes([AllowAny])
@csrf_exempt
def telegram_webhook(request):
    """
    Handles incoming webhooks from Telegram.
    This function processes messages, specifically the '/start' command,
    to link a user's Telegram chat ID to their Django user account.

    """
    print("WEBHOOK FUNCTION IS CALLED")
    try:

        update = request.data
        print("Received Telegram webhook update:", update)
        message = update.get("message", {})
        text = message.get("text", "")
        chat = message.get("chat", {})

        chat_id = chat.get("id")
        print("Chat ID:", chat_id)

        if not chat_id:
            # Обробляємо випадок, коли chat_id відсутній у payload.
            return Response(
                {"error": "No chat_id found in webhook payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Перевіряємо, чи починається повідомлення з команди '/start'.
        if text.startswith("/start"):
            parts = text.split(" ")

            # Випадок 1: Команда '/start' супроводжується токеном.
            if len(parts) > 1:
                token = parts[1]

                try:
                    # Витягуємо ID користувача з рядка токена.
                    user_id = int(token.split("-")[-1])
                    User = get_user_model()
                    user = User.objects.get(id=user_id)

                    # Прив'язуємо ID чату Telegram до користувача.
                    user.telegram_chat_id = chat_id
                    user.save()

                    # Надсилаємо повідомлення про успішне прив'язування.
                    send_telegram_message(
                        chat_id, "<b>Your account has been successfully linked!</b>"
                    )
                    return Response(status=status.HTTP_200_OK)
                except (ValueError, User.DoesNotExist) as e:
                    # Обробляємо випадки, коли токен є недійсним або користувач не існує.
                    send_telegram_message(chat_id, "Error: Invalid token.")
                    return Response(status=status.HTTP_400_BAD_REQUEST)

            # Випадок 2: Команда '/start' надіслана без токена.
            else:
                response_message = (
                    "Hello! To link your account, please use the special "
                    "link provided in your user profile."
                )
                # Надсилаємо повідомлення, щоб скерувати користувача.
                if send_telegram_message(chat_id, response_message):
                    return Response(status=status.HTTP_200_OK)
                else:
                    return Response(
                        {"error": "Failed to send message"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

        else:
            # Обробка інших повідомлень.
            send_telegram_message(
                chat_id, "I'm sorry, I don't understand that command."
            )
            return Response(status=status.HTTP_200_OK)

    except Exception as e:
        # Catch any unexpected errors during webhook processing.
        print(f"An unexpected error occurred: {e}")
        return Response(
            {"error": "Internal Server Error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
