from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from services.models import Category, Service, TimeSlot
from bookings.models import Booking, Payment

User = get_user_model()


class BookingAPITest(APITestCase):    
    def setUp(self):
        Booking.objects.all().delete()
        TimeSlot.objects.all().delete()
        Service.objects.all().delete()
        Category.objects.all().delete()
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='customer123',
            role=User.Roles.CUSTOMER
        )
        
        self.provider = User.objects.create_user(
            username='provider',
            email='provider@test.com',
            password='provider123',
            role=User.Roles.SERVICE_PROVIDER
        )
        
        self.provider2 = User.objects.create_user(
            username='provider2',
            email='provider2@test.com',
            password='provider123',
            role=User.Roles.SERVICE_PROVIDER
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role=User.Roles.ADMIN,
            is_staff=True
        )
        
        self.category = Category.objects.create(
            name='آرایشی',
            slug='beauty',
            is_active=True
        )
        
        self.service = Service.objects.create(
            provider=self.provider,
            title='کاشت ناخن',
            description='خدمات حرفه‌ای',
            price=250000,
            duration_minutes=90,
            is_active=True,
            category=self.category
        )
        
        self.now = timezone.now()
        self.start_time = self.now + timedelta(days=2, hours=10)
        self.end_time = self.start_time + timedelta(minutes=90)
        
        self.time_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.start_time,
            end_time=self.end_time,
            is_active=True,
            is_booked=False
        )
        
        self.booking = Booking.objects.create(
            customer=self.customer,
            provider=self.provider,
            service=self.service,
            time_slot=self.time_slot,
            price_at_booking=250000,
            status=Booking.Status.PENDING,
            payment_status=Booking.PaymentStatus.UNPAID
        )
        
        self.time_slot.is_booked = True
        self.time_slot.save()
    
    def test_create_booking_as_customer(self):
        self.client.login(username='customer', password='customer123')
        
        new_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=3, hours=10),
            end_time=self.now + timedelta(days=3, hours=11, minutes=30),
            is_active=True,
            is_booked=False
        )
        
        url = '/api/bookings/bookings/'
        data = {
            'time_slot': new_slot.id,
            'customer_note': 'لطفاً زنگ بزنید'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_booking_as_provider_fails(self):
        self.client.login(username='provider', password='provider123')
        
        new_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=3, hours=10),
            end_time=self.now + timedelta(days=3, hours=11, minutes=30),
            is_active=True,
            is_booked=False
        )
        
        url = '/api/bookings/bookings/'
        data = {'time_slot': new_slot.id}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_booking_with_inactive_slot_fails(self):
        self.client.login(username='customer', password='customer123')
        
        inactive_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=3, hours=10),
            end_time=self.now + timedelta(days=3, hours=11, minutes=30),
            is_active=False,
            is_booked=False
        )
        
        url = '/api/bookings/bookings/'
        data = {'time_slot': inactive_slot.id}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_booking_with_booked_slot_fails(self):
        self.client.login(username='customer', password='customer123')
        
        booked_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=3, hours=10),
            end_time=self.now + timedelta(days=3, hours=11, minutes=30),
            is_active=True,
            is_booked=True
        )
        
        url = '/api/bookings/bookings/'
        data = {'time_slot': booked_slot.id}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_bookings_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/bookings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_list_bookings_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/bookings/bookings/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_list_bookings_as_admin(self):
        self.client.login(username='admin', password='admin123')
        url = '/api/bookings/bookings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_list_bookings_as_other_provider(self):
        self.client.login(username='provider2', password='provider123')
        url = '/api/bookings/bookings/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
    
    def test_booking_detail_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.booking.id)
    
    def test_booking_detail_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/bookings/bookings/{self.booking.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_booking_detail_as_other_provider_fails(self):
        self.client.login(username='provider2', password='provider123')
        url = f'/api/bookings/bookings/{self.booking.id}/'
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_confirm_booking_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/bookings/bookings/{self.booking.id}/confirm/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)
    
    def test_confirm_booking_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/confirm/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reject_booking_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/bookings/bookings/{self.booking.id}/reject/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.REJECTED)
    
    def test_reject_booking_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/reject/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cancel_booking_as_customer(self):
        self.booking.confirm()
        self.booking.refresh_from_db()
        
        self.client.login(username='customer', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/cancel/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.CANCELED)
    
    def test_cancel_booking_as_provider_fails(self):
        self.booking.confirm()
        
        self.client.login(username='provider', password='provider123')
        url = f'/api/bookings/bookings/{self.booking.id}/cancel/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_cancel_info(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/cancel_info/'
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('can_cancel', response.data)
    
    def test_my_bookings_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/bookings/my_bookings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_my_bookings_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/bookings/bookings/my_bookings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_booking_stats_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/bookings/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)
    
    def test_booking_stats_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/bookings/bookings/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)


class PaymentAPITest(APITestCase):    
    def setUp(self):
        Payment.objects.all().delete()
        Booking.objects.all().delete()
        TimeSlot.objects.all().delete()
        Service.objects.all().delete()
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='customer123',
            role=User.Roles.CUSTOMER
        )
        
        self.provider = User.objects.create_user(
            username='provider',
            email='provider@test.com',
            password='provider123',
            role=User.Roles.SERVICE_PROVIDER
        )
        
        self.service = Service.objects.create(
            provider=self.provider,
            title='کاشت ناخن',
            description='خدمات حرفه‌ای',
            price=250000,
            duration_minutes=90,
            is_active=True
        )
        
        self.now = timezone.now()
        self.time_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=2, hours=10),
            end_time=self.now + timedelta(days=2, hours=11, minutes=30),
            is_active=True,
            is_booked=True
        )
        
        self.booking = Booking.objects.create(
            customer=self.customer,
            provider=self.provider,
            service=self.service,
            time_slot=self.time_slot,
            price_at_booking=250000,
            status=Booking.Status.CONFIRMED,
            payment_status=Booking.PaymentStatus.UNPAID
        )
    
    def test_create_payment_success(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/payments/create_payment/'
        data = {
            'booking': self.booking.id,
            'card_number': '1234567812345678',
            'card_holder_name': 'ALI REZAEI'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.payment_status, Booking.PaymentStatus.PAID)
    
    def test_create_payment_twice_fails(self):
        Payment.objects.create(
            booking=self.booking,
            amount=250000,
            transaction_id='TEST123456789',
            is_successful=True,
            card_number='1234567812345678',
            card_holder_name='ALI REZAEI'
        )
        self.booking.mark_paid()
        
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/payments/create_payment/'
        data = {
            'booking': self.booking.id,
            'card_number': '1234567812345678',
            'card_holder_name': 'ALI REZAEI'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_payment_for_unconfirmed_booking_fails(self):
        self.booking.status = Booking.Status.PENDING
        self.booking.save()
        
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/payments/create_payment/'
        data = {
            'booking': self.booking.id,
            'card_number': '1234567812345678',
            'card_holder_name': 'ALI REZAEI'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_payment_as_provider_fails(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/bookings/payments/create_payment/'
        data = {
            'booking': self.booking.id,
            'card_number': '1234567812345678',
            'card_holder_name': 'ALI REZAEI'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_payments_as_customer(self):
        Payment.objects.create(
            booking=self.booking,
            amount=250000,
            transaction_id='TEST123456789',
            is_successful=True,
            card_number='1234567812345678',
            card_holder_name='ALI REZAEI'
        )
        
        self.client.login(username='customer', password='customer123')
        url = '/api/bookings/payments/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_payment_info(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/payment_info/'
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], 250000)



class PDFReportTest(APITestCase):
    def setUp(self):
        Booking.objects.all().delete()
        Payment.objects.all().delete()
        TimeSlot.objects.all().delete()
        Service.objects.all().delete()
        Category.objects.all().delete()
        
        self.customer = User.objects.create_user(
            username='customer_pdf',
            email='customer_pdf@test.com',
            password='customer123',
            role=User.Roles.CUSTOMER
        )
        
        self.provider = User.objects.create_user(
            username='provider_pdf',
            email='provider_pdf@test.com',
            password='provider123',
            role=User.Roles.SERVICE_PROVIDER
        )
        
        self.admin = User.objects.create_user(
            username='admin_pdf',
            email='admin_pdf@test.com',
            password='admin123',
            role=User.Roles.ADMIN,
            is_staff=True
        )
        
        self.other_user = User.objects.create_user(
            username='other_pdf',
            email='other_pdf@test.com',
            password='other123',
            role=User.Roles.CUSTOMER
        )
        
        self.category = Category.objects.create(
            name='آرایشی',
            slug='beauty',
            is_active=True
        )
        
        self.service = Service.objects.create(
            provider=self.provider,
            title='کاشت ناخن',
            description='خدمات حرفه‌ای',
            price=250000,
            duration_minutes=90,
            is_active=True,
            category=self.category
        )
        
        self.now = timezone.now()
        self.time_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=2, hours=10),
            end_time=self.now + timedelta(days=2, hours=11, minutes=30),
            is_active=True,
            is_booked=True
        )
        
        self.booking = Booking.objects.create(
            customer=self.customer,
            provider=self.provider,
            service=self.service,
            time_slot=self.time_slot,
            price_at_booking=250000,
            status=Booking.Status.CONFIRMED,
            payment_status=Booking.PaymentStatus.PAID
        )
        
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount=250000,
            transaction_id='TEST123456789',
            is_successful=True,
            card_number='1234567812345678',
            card_holder_name='ALI REZAEI'
        )
    
    def test_export_customer_pdf_as_customer(self):
        self.client.login(username='customer_pdf', password='customer123')
        url = '/api/bookings/bookings/export_customer_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
    
    def test_export_customer_pdf_as_other_user_fails(self):
        self.client.login(username='other_pdf', password='other123')
        url = '/api/bookings/bookings/export_customer_pdf/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_export_provider_pdf_as_provider(self):
        self.client.login(username='provider_pdf', password='provider123')
        url = '/api/bookings/bookings/export_provider_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_export_provider_pdf_as_customer_fails(self):
        self.client.login(username='customer_pdf', password='customer123')
        url = '/api/bookings/bookings/export_provider_pdf/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_admin_stats_pdf_as_admin(self):
        self.client.login(username='admin_pdf', password='admin123')
        url = '/api/bookings/bookings/export_admin_stats_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_export_admin_stats_pdf_as_customer_fails(self):
        self.client.login(username='customer_pdf', password='customer123')
        url = '/api/bookings/bookings/export_admin_stats_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_invoice_pdf_as_customer(self):
        self.client.login(username='customer_pdf', password='customer123')
        url = f'/api/bookings/bookings/{self.booking.id}/export_invoice_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_export_invoice_pdf_as_provider(self):
        self.client.login(username='provider_pdf', password='provider123')
        url = f'/api/bookings/bookings/{self.booking.id}/export_invoice_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_export_invoice_pdf_as_admin(self):
        self.client.login(username='admin_pdf', password='admin123')
        url = f'/api/bookings/bookings/{self.booking.id}/export_invoice_pdf/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_export_invoice_pdf_as_other_user_fails(self):
        self.client.login(username='other_pdf', password='other123')
        url = f'/api/bookings/bookings/{self.booking.id}/export_invoice_pdf/'
        response = self.client.get(url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_export_invoice_pdf_for_unpaid_booking_fails(self):
        unpaid_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=3, hours=10),
            end_time=self.now + timedelta(days=3, hours=11, minutes=30),
            is_active=True,
            is_booked=True
        )
        
        unpaid_booking = Booking.objects.create(
            customer=self.customer,
            provider=self.provider,
            service=self.service,
            time_slot=unpaid_slot,
            price_at_booking=250000,
            status=Booking.Status.CONFIRMED,
            payment_status=Booking.PaymentStatus.UNPAID
        )
        
        self.client.login(username='customer_pdf', password='customer123')
        url = f'/api/bookings/bookings/{unpaid_booking.id}/export_invoice_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'این رزرو پرداخت نشده است')
    
    def test_customer_without_bookings_pdf_fails(self):
        empty_customer = User.objects.create_user(
            username='empty_customer',
            email='empty@test.com',
            password='empty123',
            role=User.Roles.CUSTOMER
        )
        
        self.client.login(username='empty_customer', password='empty123')
        url = '/api/bookings/bookings/export_customer_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'هیچ رزروی برای شما وجود ندارد')
    
    def test_provider_without_bookings_pdf_fails(self):
        empty_provider = User.objects.create_user(
            username='empty_provider',
            email='empty_provider@test.com',
            password='empty123',
            role=User.Roles.SERVICE_PROVIDER
        )
        
        self.client.login(username='empty_provider', password='empty123')
        url = '/api/bookings/bookings/export_provider_pdf/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'هیچ رزروی برای شما وجود ندارد')