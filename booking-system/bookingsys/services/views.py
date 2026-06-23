from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import Category, Service, TimeSlot
from .serializers import (
    CategorySerializer, ServiceSerializer, 
    ServiceCreateUpdateSerializer, TimeSlotSerializer
)
from users.permissions import IsProviderOrAdmin


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['name']


class ServiceViewSet(viewsets.ModelViewSet):
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active', 'provider']
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at', 'duration_minutes']
    ordering = ['-created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        if self.action == 'available_slots':
            return [AllowAny()]
        return [IsAuthenticated(), IsProviderOrAdmin()]
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Service.objects.filter(is_active=True)
        if user.is_admin:
            return Service.objects.all()
        if user.is_provider:
            return Service.objects.filter(provider=user)
        return Service.objects.filter(is_active=True)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ServiceCreateUpdateSerializer
        return ServiceSerializer
    
    def perform_create(self, serializer):
        serializer.save(provider=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        service = self.get_object()
        
        if service.time_slots.filter(is_booked=True).exists():
            return Response(
                {'error': 'این سرویس دارای رزرو است و قابل حذف نمی‌باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def available_slots(self, request, pk=None):
        try:
            service = Service.objects.get(pk=pk, is_active=True)
        except Service.DoesNotExist:
            return Response({'error': 'سرویس یافت نشد'}, status=status.HTTP_404_NOT_FOUND)
        
        slots = TimeSlot.objects.filter(
            service=service,
            is_active=True, 
            is_booked=False,
            start_time__gt=datetime.now()
        ).order_by('start_time')
        
        serializer = TimeSlotSerializer(slots, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_services(self, request):
        if not request.user.is_provider:
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        services = Service.objects.filter(provider=request.user)
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)


class TimeSlotViewSet(viewsets.ModelViewSet): 
    serializer_class = TimeSlotSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['service', 'is_booked', 'is_active']
    
    def get_permissions(self):
        if self.action == 'list':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return TimeSlot.objects.filter(is_active=True, is_booked=False)
        if user.is_admin:
            return TimeSlot.objects.all()
        if user.is_provider:
            return TimeSlot.objects.filter(service__provider=user)
        return TimeSlot.objects.filter(is_active=True, is_booked=False)
    
    def create(self, request, *args, **kwargs):
        service_id = request.data.get('service')
        
        if not service_id:
            return Response(
                {'error': 'service الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist:
            return Response(
                {'error': 'سرویس یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not (request.user.is_admin or request.user == service.provider):
            return Response(
                {'error': 'شما دسترسی به این سرویس ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        slot = self.get_object()
        
        if not (request.user.is_admin or request.user == slot.service.provider):
            return Response(
                {'error': 'شما دسترسی ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if slot.is_booked:
            return Response(
                {'error': 'این بازه رزرو شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        slot.is_active = not slot.is_active
        slot.save()
        
        return Response({
            'success': True,
            'is_active': slot.is_active,
        })
    
    @action(detail=True, methods=['delete'])
    def delete_if_not_booked(self, request, pk=None):
        slot = self.get_object()
        
        if slot.is_booked:
            return Response(
                {'error': 'این بازه زمانی رزرو شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        slot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
        