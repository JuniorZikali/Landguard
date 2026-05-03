from django.urls import path

from . import views

app_name = 'verification'

urlpatterns = [
    path('deed-check/', views.deed_check_view, name='deed_check'),
    path('buyer-report/', views.buyer_report_view, name='buyer_report'),
    path('my-verifications/', views.my_verifications, name='my_verifications'),
    path('report-fraud/', views.fraud_report_create, name='fraud_report'),
    path('report-fraud/thanks/', views.fraud_report_thanks, name='fraud_report_thanks'),
]
