from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from user.models import Users
from user.serializers import UserSerializer

# Create your views here.


class UserRegisterViews(generics.CreateAPIView):
    serializer_class = UserSerializer
    authentication_classes = ()
    permission_classes = (AllowAny,)


class ManageUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user
