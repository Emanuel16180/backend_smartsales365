# apps/sales/utils.py
import threading
import logging
from django.core.mail import send_mail
from django.conf import settings
from apps.users.models import User #

# Configura un logger para ver los errores de email si ocurren
logger = logging.getLogger(__name__)

class EmailThread(threading.Thread):
    """
    Clase para enviar emails en un hilo separado (asíncrono)
    para no bloquear la respuesta del webhook.
    """
    def __init__(self, subject, message, recipient_list):
        self.subject = subject
        self.message = message
        self.recipient_list = recipient_list
        threading.Thread.__init__(self)

    def run(self):
        try:
            send_mail(
                self.subject,
                self.message,
                settings.DEFAULT_FROM_EMAIL,
                self.recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email de alerta de stock enviado a {self.recipient_list}")
        except Exception as e:
            # Registra cualquier error que ocurra en el hilo (ej. contraseña de app incorrecta)
            logger.error(f"FALLO AL ENVIAR EMAIL (hilo): {e}")

def send_low_stock_alert(product):
    """
    Busca a todos los empleados (Admins) y les envía la alerta de stock bajo.
    """
    
    # 1. Busca a todos los usuarios que tengan el rol 'EMPLOYEE'
    admin_emails = User.objects.filter(
        role=User.Role.EMPLOYEE, 
        is_active=True
    ).values_list('email', flat=True)
    
    recipient_list = list(admin_emails)
    
    if not recipient_list:
        logger.warning(f"Alerta de stock bajo para {product.name}, pero no se encontraron emails de empleados.")
        return

    # 2. Prepara el mensaje del correo
    subject = f"¡ALERTA DE STOCK BAJO! - {product.name}"
    message = f"""
    Hola equipo de SmartSales365,

    El stock del producto '{product.name}' (ID: {product.id}) ha alcanzado un nivel crítico.

    Stock Actual: {product.stock} unidades.

    Por favor, contactar al proveedor para reabastecer el inventario.

    - Sistema Automático de Alertas
    """
    
    # 3. Inicia el hilo para enviar el email sin bloquear
    logger.info(f"Disparando alerta de stock bajo para {product.name} a {len(recipient_list)} administradores.")
    EmailThread(subject, message, recipient_list).start()