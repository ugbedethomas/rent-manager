from django.urls import path
from . import views

urlpatterns = [
    path('', views.tenant_list, name='tenant_list'),
    path('status/<str:filter>/', views.tenant_list, name='tenant_list_filtered'),  # 🔍 Filter view
    path('add/', views.add_tenant, name='add_tenant'),
    path('edit/<int:tenant_id>/', views.edit_tenant, name='edit_tenant'),
    path('delete/<int:tenant_id>/', views.delete_tenant, name='delete_tenant'),
    path('dashboard/', views.dashboard, name='dashboard'),  # 📊 Dashboard summary
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/csv/', views.export_tenants_csv, name='export_csv'),
    path('renew/<int:tenant_id>/', views.renew_rent, name='renew_rent'),
    path('invoice/<int:tenant_id>/', views.generate_invoice, name='generate_invoice'),
    path('export/pdf/', views.export_tenant_list_pdf, name='export_tenant_list_pdf'),

]
