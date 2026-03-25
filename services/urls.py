from django.urls import path
from .views import ServiceListView, ServiceDetailView

app_name = "services"

urlpatterns = [
    path("servicios/", ServiceListView.as_view(), name="service_list"),
    path("servicios/<slug:slug>/", ServiceDetailView.as_view(), name="service_detail"),
]
