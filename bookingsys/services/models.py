from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='نام دسته')
    slug = models.SlugField(unique=True, verbose_name='slug')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Service(models.Model):
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
        limit_choices_to={'role': 'service_provider'},
        verbose_name='ارائه‌دهنده'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name='دسته‌بندی'
    )
    title = models.CharField(max_length=200, verbose_name='عنوان سرویس')
    description = models.TextField(verbose_name='توضیحات')
    price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت (تومان)'
    )
    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(15), MaxValueValidator(1440)],
        verbose_name='مدت زمان (دقیقه)'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'سرویس'
        verbose_name_plural = 'سرویس‌ها'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.provider.get_full_name()}"
    
    @property
    def price_display(self):
        return f"{self.price:,} تومان"
    
    @property
    def duration_display(self):
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours} ساعت و {minutes} دقیقه"
        return f"{minutes} دقیقه"


class TimeSlot(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name='سرویس'
    )
    start_time = models.DateTimeField(verbose_name='زمان شروع')
    end_time = models.DateTimeField(verbose_name='زمان پایان')
    is_booked = models.BooleanField(default=False, verbose_name='رزرو شده')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'بازه زمانی'
        verbose_name_plural = 'بازه‌های زمانی'
        ordering = ['start_time']
        unique_together = [['service', 'start_time']]
    
    def __str__(self):
        return f"{self.service.title} - {self.start_time}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        if self.start_time >= self.end_time:
            raise ValidationError('زمان شروع باید قبل از زمان پایان باشد')
        
        conflicts = TimeSlot.objects.filter(
            service=self.service,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )
        if self.pk:
            conflicts = conflicts.exclude(pk=self.pk)
        
        if conflicts.exists():
            raise ValidationError('این بازه زمانی با بازه دیگری تداخل دارد')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)