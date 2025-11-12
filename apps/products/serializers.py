# apps/products/serializers.py
from rest_framework import serializers
from .models import Category, WarrantyProvider, Warranty, Product, Brand
from config.supabase_client import supabase
import uuid

class RecursiveCategorySerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = CategorySerializer(value, context=self.context)
        return serializer.data

class CategorySerializer(serializers.ModelSerializer):
    children = RecursiveCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'children', 'description']

class WarrantyProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarrantyProvider
        fields = ['id', 'name', 'contact_email', 'contact_phone']

class WarrantySerializer(serializers.ModelSerializer):
    provider = WarrantyProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        queryset=WarrantyProvider.objects.all(), 
        source='provider', 
        write_only=True
    )

    class Meta:
        model = Warranty
        fields = [
            'id', 'title', 'terms', 'duration_days', 
            'provider', 'provider_id'
        ]

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    warranty = WarrantySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )
    warranty_id = serializers.PrimaryKeyRelatedField(
        queryset=Warranty.objects.all(),
        source='warranty',
        write_only=True,
        required=False,
        allow_null=True
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source='brand',
        write_only=True,
        required=False,
        allow_null=True
    )
    image_url = serializers.URLField(read_only=True, allow_null=True)
    image_upload = serializers.ImageField(
        write_only=True, 
        required=False, # Opcional
        allow_null=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock',
            
            # Campos de relación
            'category', 
            'category_id',
            'warranty', 
            'warranty_id',
            'brand',
            'brand_id',
            
            # Campos de imagen
            'image_url',     
            'image_upload'   
        ]

    def _upload_image_to_supabase(self, file):
        # Tu bucket se llama 'products_images'
        bucket_name = "products_image"
        
        # Genera un nombre de archivo único para evitar colisiones
        # ej: products/f9e5b6f3-f8f6-4f8e-b8d9-f8f6f8f6f8f6.jpg
        file_ext = file.name.split('.')[-1]
        file_path = f"products/{uuid.uuid4()}.{file_ext}"
        
        try:
            # Sube el archivo
            supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file.read(), # Lee el contenido del archivo
                file_options={"content-type": file.content_type}
            )
            
            # Obtiene la URL pública
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
            return public_url
        
        except Exception as e:
            print(f"Error al subir a Supabase: {e}")
            # Devuelve un error claro al frontend
            raise serializers.ValidationError(f"Error al subir imagen: {e}")

    def create(self, validated_data):
        """
        Sobrescribe el método CREATE
        """
        image_file = validated_data.pop('image_upload', None)
        
        if image_file:
            # Si se subió un archivo, súbelo a Supabase
            image_url = self._upload_image_to_supabase(image_file)
            if image_url:
                # Y guarda la URL en el campo 'image_url'
                validated_data['image_url'] = image_url
                
        # Crea el producto con el resto de los datos
        # (category y warranty se asignan gracias a 'source=')
        product = Product.objects.create(**validated_data)
        return product

    def update(self, instance, validated_data):
        """
        Sobrescribe el método UPDATE
        """
        image_file = validated_data.pop('image_upload', None)
        
        if image_file:
            # Si se subió un NUEVO archivo...
            # (Opcional: puedes borrar el archivo antiguo de Supabase aquí)
            image_url = self._upload_image_to_supabase(image_file)
            if image_url:
                validated_data['image_url'] = image_url
        
        # Actualiza el producto con el resto de los datos
        return super().update(instance, validated_data)

class BrandSerializer(serializers.ModelSerializer):
    """ Serializador para listar, crear o modificar Marcas. """
    class Meta:
        # Asegúrate de que el modelo Brand ya esté importado
        model = Brand
        fields = '__all__'