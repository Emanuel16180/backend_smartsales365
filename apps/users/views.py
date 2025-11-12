from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, UserRegisterSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView as BaseTokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.permissions import IsAdminUser

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_object(self):
        return self.request.user

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class CustomTokenObtainPairView(BaseTokenObtainPairView):
    pass

class CustomerListView(generics.ListAPIView):
    """
    Endpoint (Solo Admin) para listar todos los usuarios
    que tienen el rol de 'CUSTOMER'.
    """
    # 1. Permiso: Solo administradores (o 'is_staff=True')
    permission_classes = [IsAdminUser]
    
    # 2. Serializer: Usa el serializer de User que ya tienes
    serializer_class = UserSerializer

    # 3. Queryset: Define el filtro
    def get_queryset(self):
        # Filtra el modelo User por el rol 'CUSTOMER'
        return User.objects.filter(role=User.Role.CUSTOMER).order_by('email')