# bookings/reports.py
from django.utils import timezone
from django.db.models import Sum
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO

from .models import Booking
from services.models import Service
from users.models import User

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import arabic_reshaper
from bidi.algorithm import get_display

from django.conf import settings
import os

FONT_PATH = os.path.join(settings.BASE_DIR, 'fonts', 'Vazir.ttf')

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('Vazir', FONT_PATH))
    else:
        print(" هشدار: فایل فونت Vazir پیدا نشد! لطفاً فایل Vazir.ttf را در پوشه 'fonts' (کنار manage.py) قرار دهید.")
except Exception as e:
    print(f" خطا در بارگذاری فونت: {e}")

def fa(text):
    if text is None:
        return ""
    return get_display(arabic_reshaper.reshape(str(text)))


def create_pdf_response(pdf_content, filename):
    from django.http import HttpResponse
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def generate_customer_bookings_pdf(user, bookings):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title',
        parent=styles['Heading1'],
        fontName='Vazir',
        fontSize=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0C1844'),
        spaceAfter=15,
        textTransform='none'  
    )
    story.append(Paragraph(fa("گزارش رزروهای مشتری"), title_style))

    date_style = ParagraphStyle(
        'date',
        parent=styles['Normal'],
        fontName='Vazir',
        alignment=TA_CENTER,
        textColor=colors.grey,
        textTransform='none'
    )
    story.append(Paragraph(fa(timezone.now().strftime('%Y/%m/%d %H:%M')), date_style))
    story.append(Spacer(1, 10*mm))

    info_style = ParagraphStyle(
        'info',
        parent=styles['Normal'],
        fontName='Vazir',
        textTransform='none'
    )

    story.append(Paragraph(fa(f"نام مشتری: {user.get_full_name() or user.username}"), info_style))
    story.append(Paragraph(fa(f"ایمیل: {user.email}"), info_style))
    story.append(Paragraph(fa(f"تعداد رزروها: {bookings.count()}"), info_style))

    total_spent = bookings.filter(
        payment_status=Booking.PaymentStatus.PAID
    ).aggregate(total=Sum('price_at_booking'))['total'] or 0

    story.append(Paragraph(fa(f"جمع پرداختی: {total_spent:,.0f} تومان"), info_style))
    story.append(Spacer(1, 8*mm))

    data = [[fa('#'), fa('سرویس'), fa('تاریخ'), fa('قیمت'), fa('وضعیت'), fa('پرداخت')]]

    for idx, b in enumerate(bookings, 1):
        data.append([
            str(idx),
            fa(b.service.title),
            fa(b.time_slot.start_time.strftime('%Y/%m/%d %H:%M')),
            f"{b.price_at_booking:,.0f}",
            fa(b.get_status_display()),
            fa(b.get_payment_status_display())
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        
        ('ALIGN', (0, 0), (0, -1), 'CENTER'), 
        ('ALIGN', (1, 0), (2, -1), 'RIGHT'),  
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),   
        ('ALIGN', (4, 0), (5, -1), 'CENTER'),  
    ]))

    story.append(table)

    story.append(Spacer(1, 15*mm))
    story.append(Paragraph(fa("این گزارش توسط سیستم تولید شده است"), info_style))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_provider_bookings_pdf(user, bookings):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title',
        parent=styles['Heading1'],
        fontName='Vazir',
        fontSize=18,
        alignment=TA_CENTER,
        textTransform='none'
    )

    story.append(Paragraph(fa("گزارش رزروهای ارائه‌دهنده"), title_style))
    story.append(Spacer(1, 10*mm))

    data = [[fa('#'), fa('سرویس'), fa('مشتری'), fa('تاریخ'), fa('قیمت'), fa('وضعیت')]]

    for i, b in enumerate(bookings, 1):
        data.append([
            str(i),
            fa(b.service.title),
            fa(b.customer.get_full_name() or b.customer.username),
            fa(b.time_slot.start_time.strftime('%Y/%m/%d %H:%M')),
            f"{b.price_at_booking:,.0f}",
            fa(b.get_status_display())
        ])

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),  
        ('ALIGN', (1, 0), (3, -1), 'RIGHT'),   
        ('ALIGN', (4, 0), (4, -1), 'RIGHT'),  
        ('ALIGN', (5, 0), (5, -1), 'CENTER'), 
    ]))

    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_admin_stats_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title',
        fontName='Vazir',
        fontSize=18,
        alignment=TA_CENTER,
        textTransform='none'
    )

    story.append(Paragraph(fa("گزارش آماری سیستم"), title_style))
    story.append(Spacer(1, 10*mm))

    info_style = ParagraphStyle(
        'info',
        parent=styles['Normal'],
        fontName='Vazir',
        textTransform='none'
    )

    story.append(Paragraph(fa(f"کل کاربران: {User.objects.count()}"), info_style))
    story.append(Paragraph(fa(f"کل سرویس‌ها: {Service.objects.count()}"), info_style))
    story.append(Paragraph(fa(f"کل رزروها: {Booking.objects.count()}"), info_style))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_invoice_pdf(booking):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title',
        fontName='Vazir',
        fontSize=20,
        alignment=TA_CENTER,
        textTransform='none'
    )
    story.append(Paragraph(fa("فاکتور پرداخت"), title_style))
    story.append(Spacer(1, 10*mm))

    info = [
        [fa("مشتری"), fa(booking.customer.get_full_name() or booking.customer.username)],
        [fa("سرویس"), fa(booking.service.title)],
        [fa("تاریخ"), fa(booking.time_slot.start_time.strftime('%Y/%m/%d %H:%M'))],
        [fa("مبلغ"), f"{booking.price_at_booking:,.0f}"]
    ]

    table = Table(info)

    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))

    story.append(table)

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf