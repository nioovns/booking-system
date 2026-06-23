from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'services', views.ServiceViewSet, basename='service')
router.register(r'time-slots', views.TimeSlotViewSet, basename='timeslot')

app_name = 'services'

urlpatterns = [
    path('', include(router.urls)),
]