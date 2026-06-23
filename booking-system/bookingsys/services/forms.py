# # services/forms.py
# from django import forms
# from .models import Service, TimeSlot, Category


# class ServiceForm(forms.ModelForm):
#     """فرم ایجاد و ویرایش سرویس"""
    
#     class Meta:
#         model = Service
#         fields = ['title', 'description', 'price', 'duration_minutes', 'category', 'is_active']
#         widgets = {
#             'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان سرویس'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'توضیحات کامل سرویس'}),
#             'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'قیمت به تومان'}),
#             'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'مدت زمان به دقیقه'}),
#             'category': forms.Select(attrs={'class': 'form-control'}),
#             'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['category'].queryset = Category.objects.filter(is_active=True)
#         self.fields['category'].required = False


# class TimeSlotForm(forms.ModelForm):
#     """فرم ایجاد بازه زمانی"""
    
#     class Meta:
#         model = TimeSlot
#         fields = ['start_time', 'end_time', 'is_active']
#         widgets = {
#             'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
#             'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
#             'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
    
#     def clean(self):
#         cleaned_data = super().clean()
#         start_time = cleaned_data.get('start_time')
#         end_time = cleaned_data.get('end_time')
        
#         if start_time and end_time:
#             if start_time >= end_time:
#                 raise forms.ValidationError('زمان شروع باید قبل از زمان پایان باشد')
            
#             # بررسی مدت زمان با سرویس (اگر سرویس در context باشد)
#             if hasattr(self, 'service') and self.service:
#                 duration = (end_time - start_time).total_seconds() / 60
#                 if duration != self.service.duration_minutes:
#                     raise forms.ValidationError(
#                         f'مدت زمان بازه ({int(duration)} دقیقه) باید با مدت زمان سرویس ({self.service.duration_minutes} دقیقه) برابر باشد'
#                     )
        
#         return cleaned_data