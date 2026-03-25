# products/admin.py
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import Category, Product, ProductImage


# -----------------------------
# Inlines
# -----------------------------
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1               # 1 fila vacía por defecto
    max_num = 3             # tope de 3 imágenes por producto (consistente con tu regla de negocio)
    fields = ("image", "caption", "alt_text", "sort_order", "preview")
    readonly_fields = ("preview",)
    ordering = ("sort_order", "id")
    show_change_link = True

    @admin.display(description="Vista previa")
    def preview(self, obj):
        """
        Miniatura de ~80px. Si el archivo no tiene .url (no guardado o corrupto),
        mostramos un guion largo para no romper el admin.
        """
        if not obj or not getattr(obj, "image", None):
            return "—"
        try:
            return format_html(
                '<img src="{}" style="height:80px;width:auto;border-radius:4px;" alt="preview"/>',
                obj.image.url,
            )
        except Exception:
            return "—"


# -----------------------------
# Category
# -----------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "product_count")
    search_fields = ("name", "slug")
    ordering = ("name",)
    # En creación puedes dejar slug vacío (se autogenera por el modelo). En edición lo bloqueamos en readonly.
    prepopulated_fields = {"slug": ("name",)}  # Solo ayuda visual en "Add"; el modelo mantiene la inmutabilidad real.

    def get_readonly_fields(self, request, obj=None):
        # Slug inmutable en edición (el modelo ya valida; aquí lo reflejamos en la UI del admin)
        if obj:
            return ("slug",)
        return ()

    def get_prepopulated_fields(self, request, obj=None):
        # Evitamos usar prepopulated_fields en edición porque slug es readonly en ese modo
        if obj:
            return {}
        return self.prepopulated_fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Anotamos conteo para evitar N+1 en list_display
        return qs.annotate(_products_count=Count("products"))

    @admin.display(ordering="_products_count", description="Productos")
    def product_count(self, obj):
        return obj._products_count


# -----------------------------
# Product
# -----------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "created_at")
    list_filter = ("category", "unit", "created_at")
    search_fields = ("name", "slug", "description")
    date_hierarchy = "created_at"
    list_select_related = ("category",)  # optimiza la columna de categoría
    ordering = ("-created_at",)
    autocomplete_fields = ("category",)  # UX: autocompletar categorías

    fieldsets = (
        ("Datos básicos", {
            "fields": ("category", "name", "description"),
        }),
        ("Inventario y precio", {
            "fields": ("price", "stock"),
        }),
        ("Presentación", {
            "fields": ("weight", "unit"),
        }),
        ("URL y metadatos", {
            "fields": ("slug", "created_at", "updated_at"),
        }),
    )
    readonly_fields = ("created_at", "updated_at")  # slug lo bloqueamos sólo en edición (abajo)
    inlines = [ProductImageInline]
    save_on_top = True

    def get_readonly_fields(self, request, obj=None):
        # El slug es editable en "Add" (puedes dejarlo vacío para autogenerar).
        # En "Change" queda sólo-lectura (tu modelo lo valida como inmutable).
        ro = list(super().get_readonly_fields(request, obj))
        if obj:
            ro.append("slug")
        return tuple(ro)


# -----------------------------
# ProductImage (opcional registrar además del inline)
# -----------------------------
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "sort_order", "caption", "thumb")
    list_filter = ("product",)
    search_fields = ("product__name", "caption", "alt_text")
    ordering = ("product", "sort_order", "id")
    readonly_fields = ("thumb",)

    @admin.display(description="Miniatura")
    def thumb(self, obj):
        """
        Miniatura de ~50px para listado de imágenes.
        """
        if not obj or not getattr(obj, "image", None):
            return "—"
        try:
            return format_html(
                '<img src="{}" style="height:50px;width:auto;border-radius:3px;" alt="thumb"/>',
                obj.image.url,
            )
        except Exception:
            return "—"


# -----------------------------
# Personalización global (opcional)
# -----------------------------
admin.site.site_header = "Panel de Administración - Fumigaciones Entom"
admin.site.site_title = "Admin Fumigaciones Entom"
admin.site.index_title = "Administración"
