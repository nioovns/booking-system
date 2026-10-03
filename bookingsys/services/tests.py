from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import Category, Service, TimeSlot

User = get_user_model()


class CategoryAPITest(APITestCase):    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123',
            role=User.Roles.CUSTOMER
        )
        self.client.login(username='testuser', password='test123')
        
        self.category = Category.objects.create(
            name='آرایشی',
            slug='beauty',
            is_active=True
        )
    
    def test_list_categories(self):
        url = '/api/services/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_category_detail(self):
        url = f'/api/services/categories/{self.category.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'آرایشی')


class ServiceAPITest(APITestCase):    
    def setUp(self):
        self.provider = User.objects.create_user(
            username='provider',
            email='provider@test.com',
            password='provider123',
            role=User.Roles.SERVICE_PROVIDER
        )
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='customer123',
            role=User.Roles.CUSTOMER
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
        self.slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.now + timedelta(days=2, hours=10),
            end_time=self.now + timedelta(days=2, hours=11, minutes=30),
            is_active=True,
            is_booked=False
        )
        
    def test_list_services_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/services/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_search_services_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/services/?search=ناخن'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filter_services_by_price_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/services/?min_price=200000&max_price=300000'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_available_slots_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/services/services/{self.service.id}/available_slots/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_create_service_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/services/services/'
        data = {
            'title': 'ماساژ',
            'description': 'ماساژ حرفه‌ای',
            'price': 300000,
            'duration_minutes': 60,
            'category': self.category.id,
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'ماساژ')
    
    def test_update_service_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/services/services/{self.service.id}/'
        data = {'title': 'کاشت ناخن حرفه‌ای'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'کاشت ناخن حرفه‌ای')
    
    def test_delete_service_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/services/services/{self.service.id}/'
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_my_services_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/services/services/my_services/'
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'کاشت ناخن')
        
    def test_create_service_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/services/'
        data = {
            'title': 'ماساژ',
            'description': 'ماساژ حرفه‌ای',
            'price': 300000,
            'duration_minutes': 60,
            'category': self.category.id,
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_service_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/services/services/{self.service.id}/'
        data = {'title': 'عنوان جدید'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_service_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = f'/api/services/services/{self.service.id}/'
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_my_services_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/services/my_services/'
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_update_service_as_admin(self):
        self.client.login(username='admin', password='admin123')
        url = f'/api/services/services/{self.service.id}/'
        data = {'title': 'عنوان جدید توسط ادمین'}
        
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'عنوان جدید توسط ادمین')


class TimeSlotAPITest(APITestCase):    
    def setUp(self):
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
        
        self.customer = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='customer123',
            role=User.Roles.CUSTOMER
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
        self.start_time = self.now + timedelta(days=2, hours=10)
        self.end_time = self.start_time + timedelta(minutes=90)
        
        self.time_slot = TimeSlot.objects.create(
            service=self.service,
            start_time=self.start_time,
            end_time=self.end_time,
            is_active=True,
            is_booked=False
        )
    
    def test_list_time_slots_as_customer(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/time-slots/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_time_slot_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = '/api/services/time-slots/'
        data = {
            'service': self.service.id,
            'start_time': (self.now + timedelta(days=3, hours=14)).isoformat(),
            'end_time': (self.now + timedelta(days=3, hours=15, minutes=30)).isoformat(),
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_create_time_slot_as_other_provider_fails(self):
        self.client.login(username='provider2', password='provider123')
        url = '/api/services/time-slots/'
        data = {
            'service': self.service.id,
            'start_time': (self.now + timedelta(days=3, hours=14)).isoformat(),
            'end_time': (self.now + timedelta(days=3, hours=15, minutes=30)).isoformat(),
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_time_slot_as_customer_fails(self):
        self.client.login(username='customer', password='customer123')
        url = '/api/services/time-slots/'
        data = {
            'service': self.service.id,
            'start_time': (self.now + timedelta(days=3, hours=14)).isoformat(),
            'end_time': (self.now + timedelta(days=3, hours=15, minutes=30)).isoformat(),
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_toggle_time_slot_active_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/services/time-slots/{self.time_slot.id}/toggle_active/'
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
    
    def test_delete_time_slot_as_provider(self):
        self.client.login(username='provider', password='provider123')
        url = f'/api/services/time-slots/{self.time_slot.id}/delete_if_not_booked/'
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)