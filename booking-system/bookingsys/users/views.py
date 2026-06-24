from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, UserListSerializer
)
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import IsAdmin, IsProvider, IsCustomer 

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    # permission_classes = [IsAuthenticated]
        
    def get_permissions(self):
        if self.action in ['login', 'register']:
            return [AllowAny()]        
        if self.action == 'admin_stats':
            return [IsAdmin()]
        if self.action == 'provider_stats':
            return [IsProvider()]
        if self.action == 'customer_stats':
            return [IsCustomer()]
        
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @swagger_auto_schema(
        operation_description="ثبت‌نام کاربر جدید",
        request_body=UserCreateSerializer,
        responses={201: UserSerializer(), 400: "خطا در داده‌ها"}
    )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'ثبت‌نام با موفقیت انجام شد',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="ورود به سیستم",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='نام کاربری'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='رمز عبور'),
            }
        ),
        responses={200: "موفق", 401: "خطا در احراز هویت"}
    )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'message': f'خوش آمدید {user.get_full_name()}',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'role_display': user.get_role_display()
                },
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            })
        else:
            return Response({
                'success': False,
                'error': 'نام کاربری یا رمز عبور اشتباه است'
            }, status=status.HTTP_401_UNAUTHORIZED)
    @swagger_auto_schema(
        operation_description="دریافت اطلاعات کاربر جاری",
        responses={200: UserSerializer()}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="ویرایش اطلاعات کاربر جاری",
        request_body=UserUpdateSerializer,
        responses={200: UserSerializer()}
    )
    @action(detail=False, methods=['patch'])
    def update_me(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'پروفایل با موفقیت به‌روزرسانی شد',
            'user': UserSerializer(request.user).data
        })
    
    @swagger_auto_schema(
        operation_description="تغییر رمز عبور",
        request_body=ChangePasswordSerializer,
        responses={200: "موفق", 400: "خطا"}
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'message': 'رمز عبور با موفقیت تغییر کرد'})
    
    @swagger_auto_schema(
        operation_description="فعال/غیرفعال کردن کاربر (فقط ادمین)",
        responses={200: "موفق", 403: "دسترسی ممنوع"}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def toggle_active(self, request, pk=None):
        user = self.get_object()
        if user == request.user:
            return Response({'error': 'نمی‌توانید وضعیت خود را تغییر دهید'}, status=400)
        
        user.is_active = not user.is_active
        user.save()
        return Response({
            'message': f'کاربر {user.get_full_name()} {"فعال" if user.is_active else "غیرفعال"} شد',
            'is_active': user.is_active
        })
    
    @swagger_auto_schema(
        operation_description="تغییر نقش کاربر (فقط ادمین)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['role'],
            properties={
                'role': openapi.Schema(type=openapi.TYPE_STRING, enum=['admin', 'service_provider', 'customer']),
            }
        ),
        responses={200: "موفق", 400: "خطا"}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def change_role(self, request, pk=None):
        user = self.get_object()
        new_role = request.data.get('role')
        
        if user == request.user:
            return Response({'error': 'نمی‌توانید نقش خود را تغییر دهید'}, status=400)
        
        if new_role not in dict(User.Roles.choices):
            return Response({'error': 'نقش معتبر نیست'}, status=400)
        
        user.role = new_role
        user.save()
        return Response({
            'message': f'نقش کاربر به {user.get_role_display()} تغییر کرد',
            'role': user.role,
            'role_display': user.get_role_display()
        })
        
    @swagger_auto_schema(
        operation_description="آمار داشبورد ادمین (فقط ادمین)",
        responses={200: "آمار", 403: "دسترسی ممنوع"}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAdmin])
    def admin_stats(self, request):
        from django.db.models import Count, Sum
        from django.utils import timezone
        from datetime import timedelta
        from services.models import Service
        from bookings.models import Booking
        
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)
        
        return Response({
            'users': {
                'total': User.objects.count(),
                'admin': User.objects.filter(role=User.Roles.ADMIN).count(),
                'provider': User.objects.filter(role=User.Roles.SERVICE_PROVIDER).count(),
                'customer': User.objects.filter(role=User.Roles.CUSTOMER).count(),
            },
            'services': {
                'total': Service.objects.count(),
                'active': Service.objects.filter(is_active=True).count(),
                'inactive': Service.objects.filter(is_active=False).count(),
            },
            'bookings': {
                'total': Booking.objects.count(),
                'today': Booking.objects.filter(booking_date__date=today).count(),
                'week': Booking.objects.filter(booking_date__gte=week_ago).count(),
                'pending': Booking.objects.filter(status=Booking.Status.PENDING).count(),
                'confirmed': Booking.objects.filter(status=Booking.Status.CONFIRMED).count(),
                'completed': Booking.objects.filter(status=Booking.Status.COMPLETED).count(),
            },
            'income': {
                'total': Booking.objects.filter(payment_status=Booking.PaymentStatus.PAID).aggregate(total=Sum('price_at_booking'))['total'] or 0,
                'today': Booking.objects.filter(payment_status=Booking.PaymentStatus.PAID, payment_date__date=today).aggregate(total=Sum('price_at_booking'))['total'] or 0,
                'week': Booking.objects.filter(payment_status=Booking.PaymentStatus.PAID, payment_date__gte=week_ago).aggregate(total=Sum('price_at_booking'))['total'] or 0,
            },
        })

    @swagger_auto_schema(
        operation_description="آمار داشبورد ارائه‌دهنده (فقط ارائه‌دهنده)",
        responses={200: "آمار", 403: "دسترسی ممنوع"}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsProvider])
    def provider_stats(self, request):
        from services.models import Service
        from bookings.models import Booking
        from django.db.models import Sum
        
        services = Service.objects.filter(provider=request.user)
        bookings = Booking.objects.filter(provider=request.user)
        
        return Response({
            'services': {
                'total': services.count(),
                'active': services.filter(is_active=True).count(),
                'inactive': services.filter(is_active=False).count(),
            },
            'bookings': {
                'total': bookings.count(),
                'pending': bookings.filter(status=Booking.Status.PENDING).count(),
                'confirmed': bookings.filter(status=Booking.Status.CONFIRMED).count(),
                'completed': bookings.filter(status=Booking.Status.COMPLETED).count(),
            },
            'income': bookings.filter(payment_status=Booking.PaymentStatus.PAID).aggregate(total=Sum('price_at_booking'))['total'] or 0,
        })

    @swagger_auto_schema(
        operation_description="آمار داشبورد مشتری (فقط مشتری)",
        responses={200: "آمار", 403: "دسترسی ممنوع"}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsCustomer])
    def customer_stats(self, request):
        from bookings.models import Booking
        from django.db.models import Sum
        from django.utils import timezone
        
        now = timezone.now()
        bookings = Booking.objects.filter(customer=request.user)
        
        return Response({
            'bookings': {
                'total': bookings.count(),
                'upcoming': bookings.filter(time_slot__start_time__gt=now, status=Booking.Status.CONFIRMED).count(),
                'completed': bookings.filter(status=Booking.Status.COMPLETED).count(),
                'pending': bookings.filter(status=Booking.Status.PENDING).count(),
            },
            'total_spent': bookings.filter(payment_status=Booking.PaymentStatus.PAID).aggregate(total=Sum('price_at_booking'))['total'] or 0,
            'recent_bookings': [
                {'id': b.id, 'service_title': b.service.title, 'date': b.booking_date, 'price': b.price_at_booking}
                for b in bookings.order_by('-booking_date')[:5]
            ],
        })