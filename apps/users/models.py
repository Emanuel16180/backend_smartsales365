from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El Email debe ser proporcionado'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        extra_fields.setdefault('role', User.Role.EMPLOYEE)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser debe tener is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    # --- Definición de Roles ---
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', _('Cliente')
        EMPLOYEE = 'EMPLOYEE', _('Trabajador')

    # El email será el campo de login
    username = None 
    email = models.EmailField(_('email address'), unique=True,
        help_text=_('Requerido. Usado para el login.')
    )

    # --- Campos de Perfil ---
    first_name = models.CharField(_('first name'), max_length=150, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
        verbose_name=_('Rol de Usuario')
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Número de Teléfono')
    )
    
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Dirección')
    )

    # --- Configuración del Modelo ---
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    objects = CustomUserManager()

    class Meta:
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.role == self.Role.EMPLOYEE:
            self.is_staff = True
        else:
            self.is_staff = False
        
        if self.is_superuser:
            self.is_staff = True
            self.role = self.Role.EMPLOYEE

        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"