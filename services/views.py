from django.views.generic import ListView, DetailView
from django.core.paginator import InvalidPage

from .models import Service


class ServiceListView(ListView):
    """
    Listado principal de servicios.
    - Paginado (12 por página)
    - Optimizado para evitar N+1
    - only(...) para reducir columnas en listados
    """
    model = Service
    template_name = "services/service_list.html"
    context_object_name = "services"
    paginate_by = 12

    def get_queryset(self):
        qs = Service.objects.only(
            "id",
            "name",
            "slug",
            "description",
            "price",
            "image",
            "service_type",
        )
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


class ServiceDetailView(DetailView):
    """
    Detalle de servicio obtenido por slug.
    """
    model = Service
    template_name = "services/service_detail.html"
    context_object_name = "service"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Service.objects.only(
            "id",
            "name",
            "slug",
            "description",
            "price",
            "image",
            "service_type",
            "method",
            "estimated_time",
            "materials_description",
            "benefits",
            "recommended_for",
        )