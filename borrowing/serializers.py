from datetime import date

from jsonschema.validators import validate
from rest_framework import serializers

from borrowing.models import Borrowing
from book.models import Book
from book.serializers import BookSerializer
from user.serializers import UserSerializer
from django.db import transaction


class BorrowingCreateSerializer(serializers.ModelSerializer):
    book = serializers.SlugRelatedField(
        queryset=Book.objects.all(), slug_field="title", label="name book"
    )

    class Meta:
        model = Borrowing
        fields = ("expected_return_date", "book")

    def validate(self, data):
        book = data.get("book")
        if book.inventory == 0:
            raise serializers.ValidationError("no books available")

        # data["book"] = book
        return data

    def create(self, validated_data):
        with transaction.atomic():
            book = validated_data.pop("book")

            book.inventory -= 1
            book.save()

            request_user = self.context["request"].user
            inventory_instance = Borrowing.objects.create(
                user=request_user,
                book=book,
                expected_return_date=validated_data["expected_return_date"],
            )
            return inventory_instance


class BorrowingListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )

    def get_user(self, obj):
        # Повертаємо словник з id та email користувача
        return {"id": obj.user.id, "email": obj.user.email}


class BorrowingDetailSerializer(serializers.ModelSerializer):
    book = BookSerializer(many=False, read_only=True)
    user = UserSerializer(many=False, read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )

    def validate_expected_return_date(self, value):
        if value < date.today():
            raise serializers.ValidationError(
                {
                    "expected_return_date": "The expected return date"
                    " cannot be in the past."
                }
            )
        return value
