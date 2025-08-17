from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """
    Дозволяє доступ лише власнику об'єкта або адміністратору.
    """

    def has_object_permission(self, request, view, obj):
        # Дозволяємо GET, HEAD, OPTIONS
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True

        # Дозволяємо, якщо користувач - адміністратор
        if request.user.is_staff:
            return True

        # Дозволяємо, якщо користувач - власник об'єкта
        return obj.user == request.user
