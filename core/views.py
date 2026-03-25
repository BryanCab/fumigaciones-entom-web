from django.shortcuts import render
from products.models import Product
from services.models import Service

def home(request):
    # Productos y servicios destacados en la vista
    productos = Product.objects.prefetch_related("images").all()[:4]
    servicios = Service.objects.all()[:4]

    return render(request, 'core/home.html', {
        'productos': productos,
        'servicios': servicios,
    })
