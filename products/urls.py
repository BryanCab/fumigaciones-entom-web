# products/urls.py
from django.urls import path

from .views import (
    ProductListView,
    ProductDetailView,
    CategoryListView,
    CategoryDetailView,
)

app_name = "products"

urlpatterns = [
    # Listado de productos (paginado y filtrable por categoría vía ?categoria=<slug>)
    path("productos/", ProductListView.as_view(), name="product_list"),

    # Detalle de producto (requerido por Product.get_absolute_url)
    path("productos/<slug:slug>/", ProductDetailView.as_view(), name="product_detail"),

    # Listado de categorías con conteo de productos
    path("categorias/", CategoryListView.as_view(), name="category_list"),

    # Detalle de categoría + grid de productos (paginado)
    path("categorias/<slug:slug>/", CategoryDetailView.as_view(), name="category_detail"),
]

__all__ = ["app_name", "urlpatterns"]