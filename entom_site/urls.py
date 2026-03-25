# entom_site/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # HOME
    path("", include("core.urls")),  
    # Rutas del app products
    path("", include(("products.urls", "products"), namespace="products")),
    # Ruta de servicios
    path("", include(("services.urls", "services"), namespace="services")),
]

# Servir archivos de MEDIA sólo en desarrollo
# En producción, configúralo con tu servidor web (Nginx/Apache/S3/CloudFront)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
