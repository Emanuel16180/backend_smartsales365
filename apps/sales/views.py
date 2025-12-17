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
from .models import Sale, SaleDetail, ActivatedWarranty, ActivatedWarranty, Coupon, Delivery
from .serializers import (
    CartItemSerializer, SaleSerializer, SaleDetailReceiptSerializer,
    ActivatedWarrantySerializer, CouponSerializer, DeliveryInfoSerializer, DeliveryOrderSerializer
)
from .utils import send_low_stock_alert
from rest_framework import viewsets
from rest_framework.decorators import action

from apps.users.permissions import IsEmployeeOrReadOnly
from django.contrib.auth import get_user_model

# Configura Stripe con tu clave secreta
stripe.api_key = settings.STRIPE_SECRET_KEY

class CouponViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de cupones para el Admin.
    Incluye endpoint 'validate' para que la App Móvil verifique códigos.
    """
    queryset = Coupon.objects.all().order_by('-id')
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

    # Endpoint extra: POST /api/v1/sales/coupons/validate/
    # Accesible para CUALQUIER persona (AllowAny) para chequear código antes de pagar
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def validate(self, request):
        code = request.data.get('code', '').strip().upper()
        try:
            coupon = Coupon.objects.get(code=code)
            if coupon.is_valid:
                return Response({
                    "valid": True,
                    "discount": coupon.discount_amount,
                    "code": coupon.code,
                    "message": "¡Cupón aplicado correctamente!"
                })
            else:
                return Response({
                    "valid": False, 
                    "error": "Este cupón ya expiró o se agotó."
                }, status=400)
        except Coupon.DoesNotExist:
            return Response({
                "valid": False, 
                "error": "Código de cupón inválido."
            }, status=404)

class CreatePaymentIntentView(APIView):
    """
    Recibe carrito y cupón (opcional).
    Valida stock, calcula descuento y crea PaymentIntent en Stripe.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Validar el carrito de entrada
        cart_data = request.data.get('cart', [])
        coupon_code = request.data.get('coupon_code', None) # <--- Recibimos el código

        cart_serializer = CartItemSerializer(data=cart_data, many=True)
        if not cart_serializer.is_valid():
            return Response(cart_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        cart = cart_serializer.validated_data
        
        # 2. Calcular el total y validar stock
        total_amount = 0
        products_for_stripe_metadata = [] 
        
        try:
            # Usamos atomic para asegurar lectura consistente del stock
            with transaction.atomic(): 
                for item in cart:
                    # Bloqueamos el producto momentáneamente para leer stock real
                    product = Product.objects.select_for_update().get(id=item['product_id'])
                    
                    if product.stock < item['quantity']:
                        return Response({"error": f"Stock insuficiente para {product.name}"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    total_amount += float(product.price) * item['quantity']
                    
                    products_for_stripe_metadata.append({
                        "id": product.id,
                        "name": product.name,
                        "quantity": item['quantity'],
                        "price": str(product.price)
                    })

            # 3. Lógica de Cupón
            discount = 0.0
            valid_coupon_id = None

            if coupon_code:
                try:
                    # Busamos el cupón (case insensitive)
                    coupon = Coupon.objects.get(code=str(coupon_code).strip().upper())
                    if coupon.is_valid:
                        discount = float(coupon.discount_amount)
                        valid_coupon_id = coupon.id
                except Coupon.DoesNotExist:
                    # Si el cupón no existe, simplemente no aplicamos descuento (o podrías retornar error)
                    pass

            # CAPTURAR INFORMACIÓN DE DELIVERY (Opcional)
            delivery_info = request.data.get('delivery_info', None)
            delivery_metadata = None

            if delivery_info:
            # Validamos que lat, long y dirección vengan bien
                delivery_serializer = DeliveryInfoSerializer(data=delivery_info)
                if delivery_serializer.is_valid():
                    # Convertimos a string JSON para meterlo en Stripe Metadata
                    delivery_metadata = json.dumps(delivery_serializer.validated_data)
                else:
                    return Response(delivery_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Calcular total final (mínimo 0)
            final_amount = total_amount - discount
            if final_amount < 0: 
                final_amount = 0

            # 4. Crear el Intento de Pago en Stripe
            intent = stripe.PaymentIntent.create(
                amount=int(final_amount * 100), # Stripe usa centavos
                currency='bob',
                metadata={
                    "user_id": request.user.id,
                    "cart": json.dumps(products_for_stripe_metadata),
                    "coupon_id": valid_coupon_id, # <--- Guardamos ID del cupón en Stripe
                    "delivery_info": delivery_metadata # <--- Guardamos info de delivery si existe
                },
                payment_method_types=['card']
            )
            
            return Response({
                'clientSecret': intent.client_secret,
                'original_total': total_amount,
                'discount': discount,
                'final_total': final_amount
            }, status=status.HTTP_200_OK)
            
        except Product.DoesNotExist:
            return Response({"error": "Uno o más productos no fueron encontrados"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- ENDPOINT 2: WEBHOOK DE STRIPE (CON USO DE CUPÓN) ---

class StripeWebhookView(APIView):
    """
    Escucha 'payment_intent.succeeded'.
    1. Verifica firma.
    2. Registra uso del Cupón (si hubo).
    3. Crea la Venta.
    4. Crea la Nota de Entrega (y asigna Repartidor automáticamente).
    5. Reduce Stock y activa Garantías.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        event = None

        # 1. Verificar firma
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 2. Manejar Pago Exitoso
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            metadata = payment_intent['metadata']
            
            user_id = metadata['user_id']
            cart = json.loads(metadata['cart'])
            total_amount = payment_intent['amount'] / 100
            
            # Recuperar Cupón
            coupon_id = metadata.get('coupon_id')
            if coupon_id == 'None': coupon_id = None

            # Recuperar Info Delivery
            delivery_info_json = metadata.get('delivery_info')
            
            products_to_check_stock = []

            try:
                with transaction.atomic():
                    
                    # A. Procesar Cupón (Incrementar uso)
                    coupon_instance = None
                    if coupon_id:
                        try:
                            coupon_instance = Coupon.objects.select_for_update().get(id=coupon_id)
                            coupon_instance.used_count += 1
                            coupon_instance.save()
                        except Coupon.DoesNotExist:
                            logger.warning(f"Cupón ID {coupon_id} no encontrado en webhook.")

                    # B. Crear la Venta (PRIMERO, para tener el ID)
                    sale = Sale.objects.create(
                        user_id=user_id,
                        total_amount=total_amount,
                        status=Sale.SaleStatus.COMPLETED,
                        stripe_payment_intent_id=payment_intent.id,
                        coupon=coupon_instance
                    )
                    
                    # C. Crear Delivery (Automatic Assignment Logic)
                    if delivery_info_json:
                        delivery_data = json.loads(delivery_info_json)
                        
                        # -- Lógica de Asignación Automática --
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        
                        # Busca el primer repartidor activo
                        assigned_driver = User.objects.filter(role=User.Role.DELIVERY, is_active=True).first()
                        
                        initial_status = Delivery.DeliveryStatus.ASSIGNED if assigned_driver else Delivery.DeliveryStatus.PENDING

                        Delivery.objects.create(
                            sale=sale, # Vinculamos a la venta recién creada
                            address=delivery_data['address'],
                            latitude=delivery_data['latitude'],
                            longitude=delivery_data['longitude'],
                            description=delivery_data.get('description', ''),
                            driver=assigned_driver, # Asigna si encontró a alguien
                            status=initial_status
                        )
                    
                    # D. Procesar Productos y Stock
                    for item in cart:
                        product = Product.objects.select_for_update().get(id=item['id'])

                        SaleDetail.objects.create(
                            sale=sale,
                            product=product,
                            quantity=item['quantity'],
                            price_at_purchase=item['price']
                        )
                        
                        if product.warranty:
                            ActivatedWarranty.objects.create(
                                user_id=user_id,
                                product=product,
                                sale=sale,
                                warranty_template=product.warranty
                            )

                        product.stock -= item['quantity']
                        product.save()
                        
                        products_to_check_stock.append(product)

                # --- FIN TRANSACCIÓN ---
                
                # 4. Enviar Alertas (Fuera de la transacción)
                for product in products_to_check_stock:
                    if product.stock <= 10:
                        send_low_stock_alert(product)

            except Exception as e:
                logger.error(f"Error procesando webhook: {e}")
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class DeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Vista para que los Repartidores vean sus entregas asignadas.
    """
    serializer_class = DeliveryOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Si es Admin, ve todas. Si es Delivery, solo las suyas.
        if user.role == user.Role.ADMIN:
            return Delivery.objects.all().order_by('-created_at')
        elif user.role == user.Role.DELIVERY:
            return Delivery.objects.filter(driver=user).order_by('-created_at')
        else:
            return Delivery.objects.none() # Clientes no ven esto por aquí

    # Endpoint para cambiar estado: PATCH /api/v1/sales/delivery/{id}/update-status/
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        delivery = self.get_object()
        new_status = request.data.get('status')

        # Validar que el status sea válido
        if new_status not in Delivery.DeliveryStatus.values:
            return Response({"error": "Estado inválido"}, status=400)

        delivery.status = new_status
        delivery.save()
        
        return Response({"message": f"Estado actualizado a {new_status}"})