from datetime import timedelta
import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required, permission_required

from .models import Tenant, RentAgreement, LoginLog
from .forms import TenantForm, RentAgreementForm
from django.core.management import call_command

# 📋 LIST + FILTER + SEARCH
@login_required
def tenant_list(request, filter=None):
    tenants = Tenant.objects.select_related('block').prefetch_related('agreements')

    search_query = request.GET.get('search', '')
    block_filter = request.GET.get('block', '')
    flat_type_filter = request.GET.get('flat_type', '')
    rent_filter = request.GET.get('filter', filter)

    data = []
    today = timezone.now().date()
    soon = today + timedelta(days=30)

    for tenant in tenants:
        latest_agreement = tenant.agreements.order_by('-date_of_expiration').first()
        if latest_agreement:
            status = "active"
            if latest_agreement.date_of_expiration < today:
                status = "expired"
            elif latest_agreement.date_of_expiration <= soon:
                status = "expiring"

            # Filters
            if rent_filter and status != rent_filter:
                continue
            if block_filter and str(tenant.block.number) != block_filter:
                continue
            if flat_type_filter and tenant.flat_type != flat_type_filter:
                continue
            if search_query and search_query.lower() not in (tenant.full_name.lower() + tenant.phone_number):
                continue

            data.append({
                'tenant': tenant,
                'agreement': latest_agreement,
                'status': status
            })

    context = {
        'data': data,
        'current_filter': rent_filter,
        'block_filter': block_filter,
        'flat_type_filter': flat_type_filter,
        'search_query': search_query,
        'blocks': Tenant.objects.values_list('block__number', flat=True).distinct(),
        'flat_types': Tenant.objects.values_list('flat_type', flat=True).distinct(),
    }

    return render(request, 'estate/tenant_list.html', context)


# ➕ ADD TENANT
@login_required
@permission_required('estate.add_tenant', raise_exception=True)
def add_tenant(request):
    if request.method == 'POST':
        tenant_form = TenantForm(request.POST)
        agreement_form = RentAgreementForm(request.POST)

        if tenant_form.is_valid() and agreement_form.is_valid():
            tenant = tenant_form.save()
            agreement = agreement_form.save(commit=False)
            agreement.tenant = tenant
            agreement.save()
            messages.success(request, "Tenant created successfully!")
            return redirect('tenant_list')
    else:
        tenant_form = TenantForm()
        agreement_form = RentAgreementForm()

    return render(request, 'estate/add_tenant.html', {
        'tenant_form': tenant_form,
        'agreement_form': agreement_form
    })


# 📝 EDIT TENANT
@login_required
@permission_required('estate.change_tenant', raise_exception=True)
def edit_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    agreement = tenant.agreements.order_by('-date_of_expiration').first()

    if request.method == 'POST':
        tenant_form = TenantForm(request.POST, instance=tenant)
        agreement_form = RentAgreementForm(request.POST, instance=agreement)

        if tenant_form.is_valid() and agreement_form.is_valid():
            tenant_form.save()
            agreement_form.save()
            messages.success(request, "Tenant updated successfully!")
            return redirect('tenant_list')
    else:
        tenant_form = TenantForm(instance=tenant)
        agreement_form = RentAgreementForm(instance=agreement)

    return render(request, 'estate/edit_tenant.html', {
        'tenant_form': tenant_form,
        'agreement_form': agreement_form,
        'tenant': tenant
    })


# ❌ DELETE TENANT
@login_required
@permission_required('estate.delete_tenant', raise_exception=True)
def delete_tenant(request, tenant_id):
    tenant = get_object_or_404(Tenant, pk=tenant_id)

    if request.method == 'POST':
        tenant.delete()
        messages.warning(request, f"{tenant.full_name} deleted.")
        return redirect('tenant_list')

    return render(request, 'estate/delete_tenant.html', {'tenant': tenant})


# 🔁 RENEW RENT
@login_required
@permission_required('estate.add_rentagreement', raise_exception=True)
def renew_rent(request, tenant_id):
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    last_agreement = tenant.agreements.order_by('-date_of_expiration').first()

    if request.method == 'POST':
        new_start = parse_date(request.POST.get('date_of_agreement'))
        new_end = parse_date(request.POST.get('date_of_expiration'))
        new_rent = request.POST.get('rent_amount')
        new_note = request.POST.get('payment_or_renewal_note')

        RentAgreement.objects.create(
            tenant=tenant,
            date_of_agreement=new_start,
            date_of_expiration=new_end,
            rent_amount=new_rent,
            payment_or_renewal_note=new_note
        )

        messages.success(request, "Rent renewed successfully!")
        return redirect('edit_tenant', tenant_id=tenant.id)

    default_start = last_agreement.date_of_expiration + timedelta(days=1)
    default_end = default_start + timedelta(days=365)

    return render(request, 'estate/renew_rent.html', {
        'tenant': tenant,
        'default_start': default_start,
        'default_end': default_end,
        'previous_rent': last_agreement.rent_amount
    })


# 📤 EXPORT CSV
@login_required
@permission_required('estate.view_tenant', raise_exception=True)
def export_tenants_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tenants.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Full Name', 'Phone', 'Flat Number', 'Block', 'Flat Type',
        'Agreement Start', 'Expiry Date', 'Rent Amount', 'Payment Note'
    ])

    tenants = Tenant.objects.select_related('block').prefetch_related('agreements')
    for tenant in tenants:
        agreement = tenant.agreements.order_by('-date_of_expiration').first()
        if agreement:
            writer.writerow([
                tenant.full_name,
                tenant.phone_number,
                tenant.flat_number,
                tenant.block.number,
                tenant.flat_type,
                agreement.date_of_agreement,
                agreement.date_of_expiration,
                agreement.rent_amount,
                agreement.payment_or_renewal_note
            ])
    return response


# 📊 DASHBOARD
@login_required
@permission_required('estate.view_tenant', raise_exception=True)
def dashboard(request):
    tenants = Tenant.objects.select_related('block').prefetch_related('agreements')

    total = active = expiring = expired = total_rent = 0
    today = timezone.now().date()
    soon = today + timedelta(days=30)

    for tenant in tenants:
        agreement = tenant.agreements.order_by('-date_of_expiration').first()
        if agreement:
            total += 1
            total_rent += agreement.rent_amount
            if agreement.date_of_expiration < today:
                expired += 1
            elif agreement.date_of_expiration <= soon:
                expiring += 1
            else:
                active += 1

    labels = []
    counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime("%b %d"))
        counts.append(RentAgreement.objects.filter(date_of_agreement=day).count())

    login_logs = LoginLog.objects.filter(timestamp__date=today).order_by('-timestamp')
    user_groups = list(request.user.groups.values_list('name', flat=True))

    context = {
        'total': total,
        'active': active,
        'expiring': expiring,
        'expired': expired,
        'total_rent': total_rent,
        'user_groups': user_groups,
        'chart_labels': labels,
        'chart_counts': counts,
        'login_logs': login_logs,
    }

    return render(request, 'estate/dashboard.html', context)


# 🧾 PDF INVOICE
@login_required
@permission_required('estate.view_rentagreement', raise_exception=True)
def generate_invoice(request, tenant_id):
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    agreement = tenant.agreements.order_by('-date_of_expiration').first()

    if not agreement:
        messages.error(request, "No agreement found for this tenant.")
        return redirect('tenant_list')

    template = get_template('estate/invoice.html')
    context = {'tenant': tenant, 'agreement': agreement}
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="invoice_{tenant.full_name}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('❌ Error generating PDF', status=500)
    return response


# 📄 EXPORT PDF Tenant List
@login_required
def export_tenant_list_pdf(request):
    response = tenant_list(request)
    context = getattr(response, 'context_data', response.context)

    template = get_template('estate/tenant_list_pdf.html')
    html = template.render(context)

    pdf_response = HttpResponse(content_type='application/pdf')
    pdf_response['Content-Disposition'] = 'filename="tenant_list.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=pdf_response)
    if pisa_status.err:
        return HttpResponse('❌ Error generating PDF', status=500)
    return pdf_response
def run_migrations(request):
    call_command('migrate')
    return HttpResponse("✅ Migrations completed.")