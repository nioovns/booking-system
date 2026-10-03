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
        self.assertEqual(response.data['user']['last_name'], 'رضایی جدید')
    
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
    
    def test_12_login_invalid_credentials(self):
        url = '/api/users/login/'
        
        invalid_username = {
            'username': 'wronguser',
            'password': 'customer123'
        }
        response = self.client.post(url, invalid_username, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
        
        invalid_password = {
            'username': 'customer',
            'password': 'wrongpass'
        }
        response = self.client.post(url, invalid_password, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
        
        empty_fields = {
            'username': '',
            'password': ''
        }
        response = self.client.post(url, empty_fields, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['success'])
    
    def test_13_user_list_permissions(self):
        admin_login = self.client.post('/api/users/login/', {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        admin_token = admin_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        admin_response = self.client.get('/api/users/')
        self.assertEqual(admin_response.status_code, status.HTTP_200_OK)
        self.assertEqual(admin_response.data['count'], 3)
        
        self.client.credentials()
        customer_login = self.client.post('/api/users/login/', {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        customer_token = customer_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {customer_token}')
        
        customer_response = self.client.get('/api/users/')
        self.assertEqual(customer_response.status_code, status.HTTP_200_OK)
        self.assertEqual(customer_response.data['count'], 1)
        self.assertEqual(customer_response.data['results'][0]['username'], 'customer')
    
    def test_14_admin_can_manage_users(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        toggle_url = f'/api/users/{self.customer.id}/toggle_active/'
        response = self.client.post(toggle_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        
        response = self.client.post(toggle_url)
        self.assertTrue(response.data['is_active'])
        
        role_url = f'/api/users/{self.customer.id}/change_role/'
        response = self.client.post(role_url, {'role': 'service_provider'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'service_provider')
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.role, User.Roles.SERVICE_PROVIDER)
    
    def test_15_customer_cannot_manage_users(self):
        customer_login = self.client.post('/api/users/login/', {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        customer_token = customer_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {customer_token}')
        
        toggle_url = f'/api/users/{self.provider.id}/toggle_active/'
        response = self.client.post(toggle_url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        
        role_url = f'/api/users/{self.provider.id}/change_role/'
        response = self.client.post(role_url, {'role': 'customer'}, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
    
    def test_16_stats_permissions(self):
        admin_login = self.client.post('/api/users/login/', {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')
        admin_token = admin_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {admin_token}')
        
        admin_stats = self.client.get('/api/users/admin_stats/')
        self.assertEqual(admin_stats.status_code, status.HTTP_200_OK)
        self.assertIn('users', admin_stats.data)
        
        self.client.credentials()
        provider_login = self.client.post('/api/users/login/', {
            'username': 'provider',
            'password': 'provider123'
        }, format='json')
        provider_token = provider_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {provider_token}')
        
        provider_stats = self.client.get('/api/users/provider_stats/')
        self.assertEqual(provider_stats.status_code, status.HTTP_200_OK)
        self.assertIn('services', provider_stats.data)
        
        self.client.credentials()
        customer_login = self.client.post('/api/users/login/', {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        customer_token = customer_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {customer_token}')
        
        customer_stats = self.client.get('/api/users/customer_stats/')
        self.assertEqual(customer_stats.status_code, status.HTTP_200_OK)
        self.assertIn('bookings', customer_stats.data)
        
        self.client.credentials()
        customer_login = self.client.post('/api/users/login/', {
            'username': 'customer',
            'password': 'customer123'
        }, format='json')
        customer_token = customer_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {customer_token}')
        
        admin_stats_access = self.client.get('/api/users/admin_stats/')
        self.assertEqual(admin_stats_access.status_code, status.HTTP_403_FORBIDDEN)
        
        provider_stats_access = self.client.get('/api/users/provider_stats/')
        self.assertEqual(provider_stats_access.status_code, status.HTTP_403_FORBIDDEN)
        
        self.client.credentials()
        provider_login = self.client.post('/api/users/login/', {
            'username': 'provider',
            'password': 'provider123'
        }, format='json')
        provider_token = provider_login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {provider_token}')
        
        customer_stats_access = self.client.get('/api/users/customer_stats/')
        self.assertEqual(customer_stats_access.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_17_admin_update_user_by_id(self):
        response = self.client.post('/api/users/login/', {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')

        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        url = f'/api/users/{self.customer.id}/'

        data = {
            'username': 'new_username',
            'role': User.Roles.SERVICE_PROVIDER,
            'password': 'newpass123'
        }

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['username'], 'new_username')
        self.assertEqual(response.data['role'], User.Roles.SERVICE_PROVIDER)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.username, 'new_username')
        self.assertTrue(self.customer.check_password('newpass123'))   

    def test_18_admin_delete_user(self):
        login_url = '/api/users/login/'
        response = self.client.post(login_url, {
            'username': 'admin',
            'password': 'admin123'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        user_id = self.customer.id
        url = f'/api/users/{user_id}/'

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=user_id).exists())