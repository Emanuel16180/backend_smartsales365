import stripe
import json
from django.conf import settings
from django.db import transaction
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from .filters import SaleFilter

from apps.products.models import Product, Warranty
from .models import Sale, SaleDetail, ActivatedWarranty, ActivatedWarranty
from .serializers import (
    CartItemSerializer, SaleSerializer, SaleDetailReceiptSerializer,
    ActivatedWarrantySerializer
)
from .utils import send_low_stock_alert

# Configura Stripe con tu clave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY

# --- ENDPOINT 1: CREAR INTENTO DE PAGO ---

class CreatePaymentIntentView(APIView):
    """
    Recibe un carrito de compras, valida el stock y crea un PaymentIntent en Stripe.
    Devuelve un 'clientSecret' al frontend.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Validar el carrito de entrada
        cart_serializer = CartItemSerializer(data=request.data.get('cart', []), many=True)
        if not cart_serializer.is_valid():
            return Response(cart_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        cart = cart_serializer.validated_data
        
        # 2. Calcular el total y validar stock EN EL BACKEND
        total_amount = 0
        products_for_stripe_metadata = [] # Guardamos info para el webhook
        
        try:
            with transaction.atomic(): # Bloqueamos la DB para chequear stock
                for item in cart:
                    product = Product.objects.select_for_update().get(id=item['product_id'])
                    
                    if product.stock < item['quantity']:
                        return Response({"error": f"Stock insuficiente para {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    total_amount += product.price * item['quantity']
                    products_for_stripe_metadata.append({
                        "id": product.id,
                        "name": product.name,
                        "quantity": item['quantity'],
                        "price": str(product.price) # Guardamos como string
                    })

            # 3. Crear el Intento de Pago en Stripe
            # Stripe maneja centavos, así que multiplicamos por 100
            intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),
                currency='bob', # O 'bob', 'mxn', etc.
                metadata={
                    "user_id": request.user.id,
                    "cart": json.dumps(products_for_stripe_metadata) # Guardamos el carrito
                },
                payment_method_types=['card']
            )
            
            # 4. Devolver el 'client_secret' al frontend
            return Response({
                'clientSecret': intent.client_secret
            }, status=status.HTTP_200_OK)
            
        except Product.DoesNotExist:
            return Response({"error": "Uno o más productos no fueron encontrados"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- ENDPOINT 2: WEBHOOK DE STRIPE ---

class StripeWebhookView(APIView):
    """
    Escucha los eventos de Stripe, principalmente 'payment_intent.succeeded'.
    Verifica la firma, crea la Venta, reduce el stock y activa garantías.
    """
    permission_classes = [AllowAny] # Debe ser pública

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        event = None

        # 1. Verificar la firma del Webhook (¡Seguridad!)
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST) # Payload inválido
        except stripe.error.SignatureVerificationError:
            return Response(status=status.HTTP_400_BAD_REQUEST) # Firma inválida

        # 2. Manejar el evento de "Pago Exitoso"
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            metadata = payment_intent['metadata']
            user_id = metadata['user_id']
            cart = json.loads(metadata['cart'])
            total_amount = payment_intent['amount'] / 100

            # --- ¡ARREGLO AQUÍ! ---
            # Define la lista ANTES del bloque 'try'
            products_to_check_stock = []
            # --- FIN DEL ARREGLO ---

            try:
                # 3. ¡Transacción Atómica!
                with transaction.atomic():
                    
                    # A. Crear la Venta (Sale)
                    sale = Sale.objects.create(
                        user_id=user_id,
                        total_amount=total_amount,
                        status=Sale.SaleStatus.COMPLETED,
                        stripe_payment_intent_id=payment_intent.id
                    )
                    
                    for item in cart:
                        product = Product.objects.select_for_update().get(id=item['id'])

                        # B. Crear el Detalle de Venta (SaleDetail)
                        SaleDetail.objects.create(
                            sale=sale,
                            product=product,
                            quantity=item['quantity'],
                            price_at_purchase=item['price']
                        )
                        
                        # C. Activar la Garantía
                        if product.warranty:
                            ActivatedWarranty.objects.create(
                                user_id=user_id,
                                product=product,
                                sale=sale,
                                warranty_template=product.warranty
                            )

                        # D. Reducir el Stock
                        product.stock -= item['quantity']
                        product.save()
                        
                        # Añade el producto actualizado a la lista
                        products_to_check_stock.append(product)

                # --- ¡FIN DE LA TRANSACCIÓN ATÓMICA! ---
                
                # --- 4. VERIFICAR STOCK Y ENVIAR ALERTA (FUERA DE LA TRANSACCIÓN) ---
                # Ahora 'products_to_check_stock' SÍ está definida
                for product in products_to_check_stock:
                    if product.stock <= 10:
                        send_low_stock_alert(product)

            except Exception as e:
                print(f"Error procesando webhook: {e}")
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 5. Confirmar a Stripe que recibimos el evento
        return Response(status=status.HTTP_200_OK)
# --- ENDPOINTS 3 y 4: VER COMPRAS Y RECIBOS ---

class MyPurchasesListView(generics.ListAPIView):
    """ Devuelve una lista de todas las compras del usuario logueado """
    permission_classes = [IsAuthenticated]
    serializer_class = SaleSerializer

    def get_queryset(self):
        # Solo muestra ventas completadas del usuario actual
        return Sale.objects.filter(
            user=self.request.user, 
            status=Sale.SaleStatus.COMPLETED
        ).order_by('-created_at')

class ReceiptDetailView(generics.RetrieveAPIView):
    """ Devuelve una "Nota de Compra" detallada (un recibo) """
    permission_classes = [IsAuthenticated]
    serializer_class = SaleDetailReceiptSerializer
    queryset = Sale.objects.all()

    def get_queryset(self):
        # El usuario solo puede ver sus propias compras
        return Sale.objects.filter(user=self.request.user).prefetch_related(
            'details__product', 
            'activated_warranties__product__brand'
        )

class MyWarrantiesListView(generics.ListAPIView):
    """
    Devuelve una lista de todas las garantías activas
    del usuario logueado, ordenadas por fecha de expiración.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ActivatedWarrantySerializer

    def get_queryset(self):
        return ActivatedWarranty.objects.filter(
            user=self.request.user
        ).select_related(
            'product', 'sale'
        ).order_by('expiration_date') # Ordena por las que expiran pronto

class AdminSaleListView(generics.ListAPIView):
    """
    (Solo Admin) Devuelve una lista de TODAS las ventas
    con filtros potentes por cliente, producto, fecha y monto.
    """
    permission_classes = [IsAdminUser]

    # --- 1. USA EL SERIALIZADOR DETALLADO ---
    serializer_class = SaleDetailReceiptSerializer 

    filter_backends = [DjangoFilterBackend]
    filterset_class = SaleFilter

    # --- 2. ASEGÚRATE DE QUE ESTA LÍNEA EXISTA ---
    queryset = Sale.objects.all().order_by('-created_at').prefetch_related(
        'user',
        'details__product',
        'activated_warranties'
    )