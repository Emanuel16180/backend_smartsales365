from rest_framework import serializers
from .models import User

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