from django_filters import rest_framework as filters
from .models import User

class UserFilter(filters.FilterSet):
    
    role = filters.ChoiceFilter(choices=User.Roles.choices)
    is_active = filters.BooleanFilter()
    date_joined_after = filters.DateFilter(field_name='date_joined', lookup_expr='gte')
    date_joined_before = filters.DateFilter(field_name='date_joined', lookup_expr='lte')
    search = filters.CharFilter(method='custom_search')
    
    class Meta:
        model = User
        fields = ['role', 'is_active']
    
    def custom_search(self, queryset, name, value):
        return queryset.filter(
            models.Q(username__icontains=value) |
            models.Q(first_name__icontains=value) |
            models.Q(last_name__icontains=value) |
            models.Q(email__icontains=value) |
            models.Q(phone_number__icontains=value)
        )