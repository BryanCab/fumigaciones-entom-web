from django.contrib import admin
from django.utils.html import format_html
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "service_type",
        "method",
        "price",
        "created_at",
        "image_preview",
    )

    search_fields = ("name", "description")
    list_filter = ("service_type", "method", "created_at")
    readonly_fields = ("slug", "created_at", "updated_at", "image_preview")

    fieldsets = (
        (
            "Información Principal",
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "price",
                    "image",
                    "image_preview",
                )
            },
        ),
        (
            "Clasificación",
            {
                "fields": (
                    "service_type",
                    "method",
                )
            },
        ),
        (
            "Contenido Adicional",
            {
                "fields": (
                    "estimated_time",
                    "materials_description",
                    "benefits",
                    "recommended_for",
                )
            },
        ),
        (
            "Tiempos",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def image_preview(self, obj):
        if not obj.image:
            return "No hay imagen"
        return format_html(
            '<img src="{}" style="width: 80px; height: auto; border-radius:5px;"/>',
            obj.image.url,
        )

    image_preview.short_description = "Vista previa"
