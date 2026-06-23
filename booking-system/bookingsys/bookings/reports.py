# bookings/reports.py
from django.utils import timezone
from django.db.models import Sum
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO

from .models import Booking
from services.models import Service
from users.models import User


def create_pdf_response(pdf_content, filename):
    """ایجاد پاسخ HTTP برای PDF"""
    from django.http import HttpResponse
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def generate_customer_bookings_pdf(user, bookings):
    """گزارش PDF رزروهای یک مشتری"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    
    # عنوان
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#0C1844'),
        alignment=TA_CENTER,
        spaceAfter=20
    )
    story.append(Paragraph("گزارش رزروهای مشتری", title_style))
    
    # تاریخ
    date_style = ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12, textColor=colors.grey)
    story.append(Paragraph(f"تاریخ: {timezone.now().strftime('%Y/%m/%d %H:%M')}", date_style))
    story.append(Spacer(1, 10*mm))
    
    # اطلاعات مشتری
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>نام مشتری:</b> {user.get_full_name() or user.username}", info_style))
    story.append(Paragraph(f"<b>ایمیل:</b> {user.email}", info_style))
    story.append(Paragraph(f"<b>تعداد کل رزروها:</b> {bookings.count()}", info_style))
    total_spent = bookings.filter(payment_status=Booking.PaymentStatus.PAID).aggregate(total=Sum('price_at_booking'))['total'] or 0
    story.append(Paragraph(f"<b>مجموع هزینه:</b> {total_spent:,.0f} تومان", info_style))
    story.append(Spacer(1, 10*mm))
    
    # جدول رزروها
    data = [['ردیف', 'سرویس', 'تاریخ', 'قیمت', 'وضعیت', 'پرداخت']]
    for idx, booking in enumerate(bookings, 1):
        data.append([
            str(idx),
            booking.service.title,
            booking.time_slot.start_time.strftime('%Y/%m/%d %H:%M'),
            f"{booking.price_at_booking:,.0f}",
            booking.get_status_display(),
            booking.get_payment_status_display()
        ])
    
    table = Table(data, colWidths=[25*mm, 50*mm, 40*mm, 30*mm, 30*mm, 30*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    
    # فوتر
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
    story.append(Paragraph("این گزارش توسط سیستم مدیریت خدمات تولید شده است.", footer_style))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_provider_bookings_pdf(user, bookings):
    """گزارش PDF رزروهای یک ارائه‌دهنده"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0C1844'), alignment=TA_CENTER, spaceAfter=20)
    story.append(Paragraph("گزارش رزروهای ارائه‌دهنده", title_style))
    
    date_style = ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12, textColor=colors.grey)
    story.append(Paragraph(f"تاریخ: {timezone.now().strftime('%Y/%m/%d %H:%M')}", date_style))
    story.append(Spacer(1, 10*mm))
    
    info_style = styles['Normal']
    story.append(Paragraph(f"<b>نام ارائه‌دهنده:</b> {user.get_full_name() or user.username}", info_style))
    story.append(Paragraph(f"<b>ایمیل:</b> {user.email}", info_style))
    story.append(Paragraph(f"<b>تعداد کل رزروها:</b> {bookings.count()}", info_style))
    total_income = bookings.filter(payment_status=Booking.PaymentStatus.PAID).aggregate(total=Sum('price_at_booking'))['total'] or 0
    story.append(Paragraph(f"<b>مجموع درآمد:</b> {total_income:,.0f} تومان", info_style))
    story.append(Spacer(1, 10*mm))
    
    data = [['ردیف', 'سرویس', 'مشتری', 'تاریخ', 'قیمت', 'وضعیت', 'پرداخت']]
    for idx, booking in enumerate(bookings, 1):
        data.append([
            str(idx),
            booking.service.title,
            booking.customer.get_full_name() or booking.customer.username,
            booking.time_slot.start_time.strftime('%Y/%m/%d %H:%M'),
            f"{booking.price_at_booking:,.0f}",
            booking.get_status_display(),
            booking.get_payment_status_display()
        ])
    
    table = Table(data, colWidths=[20*mm, 45*mm, 35*mm, 35*mm, 25*mm, 25*mm, 25*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(table)
    
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
    story.append(Paragraph("این گزارش توسط سیستم مدیریت خدمات تولید شده است.", footer_style))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_admin_stats_pdf():
    """گزارش آماری PDF برای ادمین"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#0C1844'), alignment=TA_CENTER, spaceAfter=20)
    story.append(Paragraph("گزارش آماری سیستم", title_style))
    
    date_style = ParagraphStyle('Date', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12, textColor=colors.grey)
    story.append(Paragraph(f"تاریخ: {timezone.now().strftime('%Y/%m/%d %H:%M')}", date_style))
    story.append(Spacer(1, 10*mm))
    
    # آمار کاربران
    story.append(Paragraph("<b>📊 آمار کاربران</b>", styles['Heading2']))
    total_users = User.objects.count()
    admin_count = User.objects.filter(role=User.Roles.ADMIN).count()
    provider_count = User.objects.filter(role=User.Roles.SERVICE_PROVIDER).count()
    customer_count = User.objects.filter(role=User.Roles.CUSTOMER).count()
    
    user_data = [['نوع کاربر', 'تعداد']]
    user_data.append(['کل کاربران', str(total_users)])
    user_data.append(['مدیران', str(admin_count)])
    user_data.append(['ارائه‌دهندگان', str(provider_count)])
    user_data.append(['مشتریان', str(customer_count)])
    
    user_table = Table(user_data, colWidths=[70*mm, 50*mm])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 8*mm))
    
    # آمار سرویس‌ها
    story.append(Paragraph("<b>📦 آمار سرویس‌ها</b>", styles['Heading2']))
    total_services = Service.objects.count()
    active_services = Service.objects.filter(is_active=True).count()
    inactive_services = Service.objects.filter(is_active=False).count()
    
    service_data = [['نوع سرویس', 'تعداد']]
    service_data.append(['کل سرویس‌ها', str(total_services)])
    service_data.append(['فعال', str(active_services)])
    service_data.append(['غیرفعال', str(inactive_services)])
    
    service_table = Table(service_data, colWidths=[70*mm, 50*mm])
    service_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(service_table)
    story.append(Spacer(1, 8*mm))
    
    # آمار رزروها
    story.append(Paragraph("<b>📋 آمار رزروها</b>", styles['Heading2']))
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status=Booking.Status.PENDING).count()
    confirmed_bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).count()
    completed_bookings = Booking.objects.filter(status=Booking.Status.COMPLETED).count()
    canceled_bookings = Booking.objects.filter(status=Booking.Status.CANCELED).count()
    rejected_bookings = Booking.objects.filter(status=Booking.Status.REJECTED).count()
    
    booking_data = [['وضعیت', 'تعداد']]
    booking_data.append(['کل رزروها', str(total_bookings)])
    booking_data.append(['در انتظار تأیید', str(pending_bookings)])
    booking_data.append(['تأیید شده', str(confirmed_bookings)])
    booking_data.append(['انجام شده', str(completed_bookings)])
    booking_data.append(['لغو شده', str(canceled_bookings)])
    booking_data.append(['رد شده', str(rejected_bookings)])
    
    booking_table = Table(booking_data, colWidths=[70*mm, 50*mm])
    booking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(booking_table)
    story.append(Spacer(1, 8*mm))
    
    # درآمد
    story.append(Paragraph("<b>💰 درآمد</b>", styles['Heading2']))
    total_income = Booking.objects.filter(payment_status=Booking.PaymentStatus.PAID).aggregate(total=Sum('price_at_booking'))['total'] or 0
    income_style = styles['Normal']
    story.append(Paragraph(f"<b>کل درآمد:</b> {total_income:,.0f} تومان", income_style))
    
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
    story.append(Paragraph("این گزارش توسط سیستم مدیریت خدمات تولید شده است.", footer_style))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_invoice_pdf(booking):
    """فاکتور پرداخت PDF برای یک رزرو"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#0C1844'), alignment=TA_CENTER, spaceAfter=10)
    story.append(Paragraph("فاکتور پرداخت", title_style))
    
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14, textColor=colors.grey)
    story.append(Paragraph("رسید پرداخت", subtitle_style))
    story.append(Paragraph(f"شماره فاکتور: INV-{booking.id}-{booking.booking_date.year}", subtitle_style))
    story.append(Paragraph(f"تاریخ: {timezone.now().strftime('%Y/%m/%d %H:%M')}", subtitle_style))
    story.append(Spacer(1, 10*mm))
    
    # اطلاعات
    info_data = [
        ['نام مشتری:', booking.customer.get_full_name() or booking.customer.username],
        ['ایمیل مشتری:', booking.customer.email],
        ['ارائه‌دهنده:', booking.provider.get_full_name() or booking.provider.username],
        ['نام سرویس:', booking.service.title],
        ['تاریخ سرویس:', booking.time_slot.start_time.strftime('%Y/%m/%d %H:%M')],
        ['وضعیت رزرو:', booking.get_status_display()],
        ['وضعیت پرداخت:', booking.get_payment_status_display()],
    ]
    
    info_table = Table(info_data, colWidths=[50*mm, 80*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10*mm))
    
    # جدول مبلغ
    invoice_data = [
        ['شرح', 'مبلغ (تومان)'],
        [f"هزینه سرویس {booking.service.title}", f"{booking.price_at_booking:,.0f}"],
        ['جمع کل', f"{booking.price_at_booking:,.0f}"]
    ]
    
    invoice_table = Table(invoice_data, colWidths=[80*mm, 50*mm])
    invoice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0C1844')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 2), (1, 2), colors.lightgrey),
        ('FONTNAME', (0, 2), (1, 2), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(invoice_table)
    
    # مبلغ قابل پرداخت
    story.append(Spacer(1, 10*mm))
    total_style = ParagraphStyle('Total', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#28a745'), alignment=TA_RIGHT)
    story.append(Paragraph(f"مبلغ قابل پرداخت: {booking.price_at_booking:,.0f} تومان", total_style))
    
    story.append(Spacer(1, 20*mm))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, fontSize=10, textColor=colors.grey)
    story.append(Paragraph("این فاکتور توسط سیستم مدیریت خدمات صادر شده است.", footer_style))
    
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

