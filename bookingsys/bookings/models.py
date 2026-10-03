# bookings/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


class Booking(models.Model):    
    class Status(models.TextChoices):
        PENDING = 'pending', _('در انتظار تأیید')
        CONFIRMED = 'confirmed', _('تأیید شده')
        REJECTED = 'rejected', _('رد شده')
        CANCELED = 'canceled', _('لغو شده')
        COMPLETED = 'completed', _('انجام شده')
    
    class PaymentStatus(models.TextChoices):
        UNPAID = 'unpaid', _('پرداخت نشده')
        PAID = 'paid', _('پرداخت شده')
        REFUNDED = 'refunded', _('برگشت داده شده')
    
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings_as_customer',
        limit_choices_to={'role': 'customer'},
        verbose_name=_('مشتری')
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings_as_provider',
        limit_choices_to={'role': 'service_provider'},
        verbose_name=_('ارائه‌دهنده')
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name=_('سرویس')
    )
    time_slot = models.OneToOneField(
        'services.TimeSlot',
        on_delete=models.CASCADE,
        related_name='booking',
        verbose_name=_('بازه زمانی')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('وضعیت رزرو')
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name=_('وضعیت پرداخت')
    )
    
    price_at_booking = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name=_('قیمت در زمان رزرو')
    )
    
    # زمان‌ها
    booking_date = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ رزرو'))
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاریخ پرداخت'))
    confirmed_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاریخ تأیید'))
    canceled_date = models.DateTimeField(blank=True, null=True, verbose_name=_('تاریخ لغو'))
    
    # توضیحات اضافی
    customer_note = models.TextField(blank=True, null=True, verbose_name=_('یادداشت مشتری'))
    provider_note = models.TextField(blank=True, null=True, verbose_name=_('یادداشت ارائه‌دهنده'))
    
    class Meta:
        verbose_name = _('رزرو')
        verbose_name_plural = _('رزروها')
        ordering = ['-booking_date']
        indexes = [
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['service', 'status']),
            models.Index(fields=['booking_date']),
        ]
    
    def __str__(self):
        return f"رزرو {self.service.title} توسط {self.customer.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # ذخیره قیمت در زمان رزرو
        if not self.pk and not self.price_at_booking:
            self.price_at_booking = self.service.price
        super().save(*args, **kwargs)
    
    @property
    def can_cancel(self):
        """آیا مشتری می‌تواند رزرو را لغو کند؟ (حداقل 2 ساعت قبل)"""
        if self.status in [self.Status.CANCELED, self.Status.COMPLETED]:
            return False
        
        now = timezone.now()
        cancel_deadline = self.time_slot.start_time - timedelta(hours=2)
        return now < cancel_deadline
    
    @property
    def cancel_deadline(self):
        """مهلت لغو رزرو (2 ساعت قبل از شروع)"""
        return self.time_slot.start_time - timedelta(hours=2)
    
    @property
    def time_until_cancel_deadline(self):
        """زمان باقی‌مانده تا مهلت لغو"""
        if not self.can_cancel:
            return timedelta(0)
        return self.cancel_deadline - timezone.now()
    
    @property
    def can_pay(self):
        """آیا می‌توان پرداخت کرد؟"""
        return self.payment_status == self.PaymentStatus.UNPAID and self.status == self.Status.CONFIRMED
    
    def confirm(self):
        """تأیید رزرو توسط ارائه‌دهنده"""
        self.status = self.Status.CONFIRMED
        self.confirmed_date = timezone.now()
        self.save()
    
    def reject(self):
        """رد رزرو توسط ارائه‌دهنده"""
        self.status = self.Status.REJECTED
        self.save()
        # آزاد کردن بازه زمانی
        self.time_slot.is_booked = False
        self.time_slot.save()
    
    def cancel(self, by_customer=True):
        """لغو رزرو"""
        self.status = self.Status.CANCELED
        self.canceled_date = timezone.now()
        self.save()
        # آزاد کردن بازه زمانی
        self.time_slot.is_booked = False
        self.time_slot.save()
    
    def mark_paid(self):
        """علامت‌گذاری به عنوان پرداخت شده"""
        self.payment_status = self.PaymentStatus.PAID
        self.payment_date = timezone.now()
        self.save()
    
    def complete(self):
        """انجام شدن سرویس"""
        self.status = self.Status.COMPLETED
        self.save()


class Payment(models.Model):
    """مدل پرداخت (برای شبیه‌سازی درگاه)"""
    
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='payment',
        verbose_name=_('رزرو')
    )
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name=_('مبلغ'))
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name=_('شماره تراکنش'))
    is_successful = models.BooleanField(default=False, verbose_name=_('موفق'))
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name=_('تاریخ پرداخت'))
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name=_('شماره کارت'))
    card_holder_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام دارنده کارت')
    class Meta:
        verbose_name = _('پرداخت')
        verbose_name_plural = _('پرداخت‌ها')
    
    def __str__(self):
        return f"پرداخت {self.amount} تومان - {self.transaction_id}"