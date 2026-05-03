from django.urls import path

from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.property_list, name='list'),
    path('add/', views.property_add, name='add'),
    path('<int:pk>/', views.property_detail, name='detail'),
    path('<int:pk>/edit/', views.property_edit, name='edit'),
]
