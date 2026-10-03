from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):    
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('نام کاربری الزامی است')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', self.model.Roles.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    objects = UserManager()
    
    class Roles(models.TextChoices):
        ADMIN = 'admin', _('Admin')
        SERVICE_PROVIDER = 'service_provider', _('Service provider')
        CUSTOMER = 'customer', _('Customer')

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.CUSTOMER,
        verbose_name=_("User Role")
    )
    
    first_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('first name'))
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('last name'))
    
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message=_('شماره موبایل باید با 09 شروع و 11 رقم باشد')
    )
    
    phone_number = models.CharField(  
        max_length=11,
        validators=[phone_regex],
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Phone Number')
    )
    
    email = models.EmailField(unique=True, verbose_name=_('email address'))
    
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Profile Picture')
    )
    
    @property
    def is_admin(self):
        return self.role == self.Roles.ADMIN or self.is_superuser
    
    @property
    def is_provider(self):
        return self.role == self.Roles.SERVICE_PROVIDER
    
    @property
    def is_customer(self):
        return self.role == self.Roles.CUSTOMER

    def __str__(self):
        name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        if name:
            return f"{name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name or self.username
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']  