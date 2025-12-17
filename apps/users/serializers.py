from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador para mostrar la información pública del usuario.
    """
    class Meta:
        model = User
        # Campos que se mostrarán en la API
        fields = [
            'id', 
            'email', 
            'first_name', 
            'last_name', 
            'role', 
            'phone_number', 
            'address',
            'full_name' # Usamos la @property que definimos
        ]
        # Campos que solo se deben leer, no escribir
        read_only_fields = ('id', 'role', 'full_name')


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de nuevos usuarios.
    Maneja la validación y creación del usuario.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 
            'password', 
            'first_name', 
            'last_name',
            'phone_number',
            'address',
            'role'  # Permitimos que elijan su rol al registrarse
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_role(self, value):
        """
        Validación para el campo 'role'.
        """
        if value not in [User.Role.CUSTOMER, User.Role.EMPLOYEE]:
            raise serializers.ValidationError("Rol no válido.")
        return value

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(email, password, **validated_data)
        
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Personaliza la respuesta del Login para incluir datos del usuario y su ROL.
    """
    def validate(self, attrs):
        # 1. Generar los tokens estándar (access y refresh)
        data = super().validate(attrs)

        # 2. Agregar datos personalizados al JSON de respuesta
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'full_name': f"{self.user.first_name} {self.user.last_name}", # O self.user.full_name si tienes esa propiedad
            'role': self.user.role  # <--- ¡AQUÍ ESTÁ LA CLAVE!
        }

        return data