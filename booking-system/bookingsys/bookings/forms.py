# # bookings/forms.py
# from django import forms
# from .models import Booking, Payment


# class BookingForm(forms.ModelForm):
#     """فرم ایجاد رزرو"""
    
#     class Meta:
#         model = Booking
#         fields = ['customer_note']
#         widgets = {
#             'customer_note': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'در صورت نیاز توضیحات خود را وارد کنید...'
#             }),
#         }


# # bookings/forms.py



# class PaymentForm(forms.Form):
#     """فرم شبیه‌سازی پرداخت"""
    
#     card_number = forms.CharField(
#         max_length=16,
#         label='شماره کارت',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control', 
#             'placeholder': '1234-5678-9012-3456',
#             'dir': 'ltr'
#         })
#     )
    
#     card_holder_name = forms.CharField(
#         max_length=100,
#         label='نام دارنده کارت',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control', 
#             'placeholder': 'مثلاً ALI REZAEI',
#             'dir': 'ltr'
#         })
#     )
    
#     expire_date = forms.CharField(
#         max_length=5,
#         label='تاریخ انقضا',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control', 
#             'placeholder': '12/25',
#             'dir': 'ltr'
#         })
#     )
    
#     cvv2 = forms.CharField(
#         max_length=4,
#         label='CVV2',
#         widget=forms.TextInput(attrs={
#             'class': 'form-control', 
#             'placeholder': '123',
#             'dir': 'ltr'
#         })
#     )
    
#     def clean_card_number(self):
#         card = self.cleaned_data.get('card_number')
#         # حذف خط تیره و فاصله
#         card = card.replace('-', '').replace(' ', '')
        
#         if not card.isdigit():
#             raise forms.ValidationError('شماره کارت باید عدد باشد')
        
#         if len(card) != 16:
#             raise forms.ValidationError('شماره کارت باید 16 رقم باشد')
        
#         return card
    
#     def clean_cvv2(self):
#         cvv = self.cleaned_data.get('cvv2')
#         if not cvv.isdigit():
#             raise forms.ValidationError('CVV2 باید عدد باشد')
        
#         if len(cvv) not in [3, 4]:
#             raise forms.ValidationError('CVV2 باید 3 یا 4 رقم باشد')
        
#         return cvv
    
#     def clean_expire_date(self):
#         date = self.cleaned_data.get('expire_date')
#         import re
        
#         if not re.match(r'^(0[1-9]|1[0-2])/([0-9]{2})$', date):
#             raise forms.ValidationError('فرمت تاریخ صحیح نیست. مثال: 12/25')
        
#         return date