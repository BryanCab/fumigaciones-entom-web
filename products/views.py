# products/views.py
from django.views.generic import ListView, DetailView
from django.db.models import Count
from django.core.paginator import InvalidPage

from .models import Product, Category


class ProductListView(ListView):
    """
    Listado principal de productos.
    - Paginado (12 por página)
    - Filtro opcional por categoría vía ?categoria=<slug>
    - Optimizado para evitar N+1: select_related(category) + prefetch_related(images)
    - only(...) para reducir columnas en listados
    """
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Product.objects.select_related("category")
            .prefetch_related("images")
            .only(
                "id",
                "name",
                "slug",
                "price",
                "stock",
                "category__id",
                "category__name",
                "category__slug",
            )
        )
        categoria_slug = self.request.GET.get("categoria")
        if categoria_slug:
            qs = qs.filter(category__slug=categoria_slug)
        return qs

    def paginate_queryset(self, queryset, page_size):
        """
        Manejo robusto de paginación:
        - Si ?page no es entero -> cae a página 1
        - Si ?page se pasa de rango -> cae a última página
        """
        paginator = self.get_paginator(queryset, page_size)
        page = self.request.GET.get(self.page_kwarg) or 1
        try:
            page_number = int(page)
        except (TypeError, ValueError):
            page_number = 1
        try:
            page_obj = paginator.page(page_number)
        except InvalidPage:
            page_obj = paginator.page(paginator.num_pages)
        return paginator, page_obj, page_obj.object_list, page_obj.has_other_pages()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        slug = self.request.GET.get("categoria")
        current_category = None
        if slug:
            # Sólo traemos lo mínimo necesario
            current_category = Category.objects.only("id", "name", "slug").filter(slug=slug).first()
        ctx["categoria_slug"] = slug or ""
        ctx["current_category"] = current_category
        return ctx


class ProductDetailView(DetailView):
    """
    Detalle de producto obtenido por slug.
    - Carga category e images sin N+1
    - Contexto expone images y main_image (property del modelo)
    """
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return (
            Product.objects.select_related("category")
            .prefetch_related("images")
            .only(
                "id",
                "name",
                "slug",
                "description",
                "price",
                "stock",
                "weight",
                "unit",
                "category__id",
                "category__name",
                "category__slug",
            )
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = ctx["product"]
        ctx["images"] = product.images.all()      # ya viene prefetched y ordenado
        ctx["main_image"] = product.main_image    # property en el modelo
        return ctx


class CategoryListView(ListView):
    """
    Listado de categorías con conteo de productos.
    - annotate(product_count) para evitar N+1
    - only(...) para columnas mínimas
    """
    model = Category
    template_name = "products/category_list.html"
    context_object_name = "categories"

    def get_queryset(self):
        return (
            Category.objects.annotate(product_count=Count("products"))
            .only("id", "name", "slug")
        )


class CategoryDetailView(DetailView):
    """
    Detalle de categoría + grid de productos de esa categoría (paginado).
    - Paginación robusta (12 por página)
    - Productos optimizados con select_related + prefetch_related + only
    """
    model = Category
    template_name = "products/category_detail.html"
    context_object_name = "category"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    paginate_by = 12

    def get_context_data(self, **kwargs):
        from django.core.paginator import Paginator  # import local para claridad

        ctx = super().get_context_data(**kwargs)
        category = ctx["category"]

        products_qs = (
            category.products.all()
            .select_related("category")
            .prefetch_related("images")
            .only(
                "id",
                "name",
                "slug",
                "price",
                "stock",
                "category__id",
                "category__name",
                "category__slug",
            )
        )

        paginator = Paginator(products_qs, self.paginate_by)
        page = self.request.GET.get("page") or 1
        try:
            page_number = int(page)
        except (TypeError, ValueError):
            page_number = 1
        try:
            page_obj = paginator.page(page_number)
        except InvalidPage:
            page_obj = paginator.page(paginator.num_pages)

        ctx["products"] = page_obj.object_list
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator
        ctx["is_paginated"] = page_obj.has_other_pages()
        return ctx


__all__ = [
    "ProductListView",
    "ProductDetailView",
    "CategoryListView",
    "CategoryDetailView",
]