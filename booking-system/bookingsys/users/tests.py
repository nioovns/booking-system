from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAPITest(APITestCase):    
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role=User.Roles.ADMIN,
            is_staff=True
        )
        
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
    
    def test_01_register_success(self):
        url = '/api/users/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'علی',
            'last_name': 'رضایی',
            'role': User.Roles.CUSTOMER
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)        
        self.assertEqual(response.data['user']['username'], 'newuser')
    
    def test_02_login_success(self):
        url = '/api/users/login/'
        data = {
            'username': 'customer',
            'password': 'customer123'
        }
        
        response = self.client.post(url, data, format='json')        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('access', response.data)
        self.assertEqual(response.data['user']['username'], 'customer')
    
    def test_03_me_authenticated(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Login failed")
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/me/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'customer')
    
    def test_04_user_list_admin(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 3)

    
    def test_05_user_list_non_admin(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['username'], 'customer')
    
    def test_06_update_me(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/update_me/'
        data = {
            'first_name': 'علی جدید',
            'last_name': 'رضایی جدید'
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['first_name'], 'علی جدید')
    
    def test_07_change_password(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/change_password/'
        data = {
            'old_password': 'customer123',
            'new_password': 'newpass123',
            'confirm_new_password': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'رمز عبور با موفقیت تغییر کرد')
    
    def test_08_admin_stats(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/admin_stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertEqual(response.data['users']['admin'], 1)
        self.assertEqual(response.data['users']['provider'], 1)
        self.assertEqual(response.data['users']['customer'], 1)
    
    def test_09_non_admin_cannot_access_admin_stats(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = '/api/users/admin_stats/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_10_toggle_user_active(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/users/{self.customer.id}/toggle_active/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        response = self.client.post(url)
        self.assertTrue(response.data['is_active'])
    
    def test_11_change_user_role(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = f'/api/users/{self.customer.id}/change_role/'
        data = {'role': 'service_provider'}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'service_provider')
        
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, User.Roles.SERVICE_PROVIDER)