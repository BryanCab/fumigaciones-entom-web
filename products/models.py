from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from decimal import Decimal
from django.urls import reverse  # Construye URLs por nombre desde el modelo
from django.core.exceptions import ValidationError
from django.utils.text import (
    slugify,
)  # Importamos esto para crear los slugs automáticamente


# ------------------------------------------------------------------------------------------------------
# Helper reutilizable para generar slugs únicos con sufijos -2, -3, ... (resuelve colisiones)
# Solo se usa en creación cuando no hay slug capturado, y se ajusta a max_length del campo.
def _generate_unique_slug(instance, base_value, slug_field_name="slug"):
    slug_field = instance._meta.get_field(slug_field_name)
    max_length = slug_field.max_length

    # Slug base a partir del valor (normalmente, 'name')
    base_slug = slugify(base_value or "")
    # Fallback por si name viene vacío o slugify produce cadena vacía
    if not base_slug:
        base_slug = "item"

    # Asegurar que el slug base no exceda el max_length (sin sufijos)
    base_slug = base_slug[:max_length]

    # Queryset del modelo para buscar colisiones (excluyendo el propio registro si ya existe pk)
    ModelClass = instance.__class__
    qs = ModelClass._default_manager.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)

    # Si no hay colisión, úsalo tal cual
    if not qs.filter(**{slug_field_name: base_slug}).exists():
        return base_slug

    # Si hay colisión, agregar sufijos -2, -3, ...
    suffix = 2
    while True:
        # Reservar espacio para el sufijo incluyendo el guion
        # ejemplo: "mi-producto" -> "mi-producto-2"
        candidate = f"{base_slug[: max_length - (len(str(suffix)) + 1)]}-{suffix}"
        if not qs.filter(**{slug_field_name: candidate}).exists():
            return candidate
        suffix += 1


# ------------------------------------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nombre de la categoría",
        error_messages={
            "unique": "Ya existe una categoría con ese nombre.",
        },
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        db_index=True,
    )

    def get_absolute_url(self):
        return reverse("products:category_detail", kwargs={"slug": self.slug})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guarda el slug original al instanciar (para detectar cambios)
        self._original_slug = self.slug

    # Validaciones de negocio que deben mostrar errores claros en formularios/admin
    def clean(self):
        # Slug inmutable: si intentan cambiarlo en actualización, bloquear
        if self.pk and self._original_slug and self.slug != self._original_slug:
            raise ValidationError({
                "slug": "El slug es inmutable. Si necesitas cambiar la URL, crea un redireccionamiento 301."
            })

    def save(self, *args, **kwargs):
        # Crear: si no hay slug, autogenerarlo a partir del nombre (y resolver colisiones)
        if not self.pk and not self.slug:
            self.slug = _generate_unique_slug(self, self.name, slug_field_name="slug")

        # Asegura que 'clean()' y 'validate_unique()' corran aunque no uses formularios del admin
        self.full_clean()

        super().save(*args, **kwargs)
        # Actualiza el original tras guardar correctamente
        self._original_slug = self.slug

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["name"]

    def __str__(self):
        return self.name


# ------------------------------------------------------------------------------------------------------
class Product(models.Model):

    class Unit(models.TextChoices):
        KG = "kg", "kg"
        G = "g", "g"
        L = "L", "L"
        ML = "mL", "mL"

    # Guarda el slug original al instanciar (para detectar cambios)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_slug = self.slug

    # Retorna la primera imagen según el orden por defecto de ProductImage.Meta.ordering.
    @property
    def main_image(self):
        images = self.images.all()  # si hay prefetch, esto viene del caché sin nueva query
        return images[0] if images else None

    # Relacionamos el producto con una categoría
    category = models.ForeignKey(
        Category,  # modelo al que apunta la FK
        on_delete=models.PROTECT,  # evita borrar una categoría en uso
        verbose_name="Categoría",  # etiqueta en admin
        related_name="products",  # permite hacer category.products.all()
    )

    name = models.CharField(
        max_length=100,
        verbose_name="Nombre del producto",
        unique=True,
        error_messages={
            "unique": "Ya existe un producto con ese nombre.",
        },
    )

    description = models.TextField(max_length=500, verbose_name="Descripción")

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Precio",
    )

    stock = models.PositiveIntegerField(default=0, verbose_name="Inventario")

    weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.000"))],
        verbose_name="Cantidad",
        help_text="Número de la presentación. Ej.: 1.200 (kg), 500.000 (mL), 0.750 (L).",
    )

    unit = models.CharField(
        max_length=3,
        choices=Unit.choices,
        default=Unit.KG,  # Puedes cambiar el default si prefieres
        verbose_name="Unidad",
        help_text="Selecciona la unidad de la presentación (kg, g, L, mL).",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )

    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Última actualización"
    )

    # Slug del producto para URLs como /producto/insecticida-xyz/
    slug = models.SlugField(
        max_length=150,  # un poco más largo por nombres de productos
        unique=True,  # no se repite entre productos (crea índice único en BD)
        blank=True,  # permite form vacío; lo generas en save()
        db_index=True,  # índice explícito para filtros por slug
    )

    def save(self, *args, **kwargs):
        # Crear: si no hay slug, autogenerarlo a partir del nombre (y resolver colisiones)
        if not self.pk and not self.slug:
            self.slug = _generate_unique_slug(self, self.name, slug_field_name="slug")

        # Asegura que 'clean()' y 'validate_unique()' corran aunque no uses formularios del admin
        self.full_clean()

        super().save(*args, **kwargs)
        # Actualiza el original tras guardar correctamente
        self._original_slug = self.slug

    def get_absolute_url(self):
        return reverse("products:product_detail", kwargs={"slug": self.slug})

    def clean(self):
        errors = {}

        # Slug inmutable en actualización
        if self.pk and self._original_slug and self.slug != self._original_slug:
            errors["slug"] = "El slug es inmutable. Si necesitas cambiar la URL, crea un redireccionamiento 301."

        # Si hay cantidad, debe haber unidad (no vacía)
        if self.weight is not None and not (self.unit and str(self.unit).strip()):
            errors["unit"] = "Debes seleccionar una unidad cuando capturas una cantidad."

        # Limitar descripción a 500 caracteres de forma real
        if self.description and len(self.description) > 500:
            errors["description"] = f"La descripción excede 500 caracteres (tiene {len(self.description)})."

        if errors:
            raise ValidationError(errors)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = [
            "-created_at"
        ]  # Opcional: ordenar para que los nuevos salgan primero

    def __str__(self):
        return self.name


# ------------------------------------------------------------------------------------------------------
class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="product_images/")
    caption = models.CharField("título", max_length=120, blank=True)
    alt_text = models.CharField("texto alternativo", max_length=120, blank=True)
    sort_order = models.PositiveSmallIntegerField(
        default=0,  # si no pones nada, toma 0 (primera imagen)
        validators=[  # validaciones a nivel de campo
            MinValueValidator(0),  # no permite valores menores a 0
            MaxValueValidator(2),  # no permite valores mayores a 2
        ],
        help_text="Orden en carrusel (0, 1, 2)",  # mensaje claro en admin/forms
    )

    class Meta:
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        ordering = ["sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "sort_order"],
                name="unique_sort_per_product",
            ),
        ]

    def __str__(self):
        return f"Imagen de {self.product.name} (orden {self.sort_order})"

    def clean(self):
        """Regla de negocio: máximo 3 imágenes por producto."""
        if not self.product_id:
            return
        # Al crear, si ya hay 3, bloquear
        if not self.pk and self.product.images.count() >= 3:
            raise ValidationError("Este producto ya tiene 3 imágenes.")

    def save(self, *args, **kwargs):
        # Asegura que 'clean()' corra aunque no uses formularios del admin
        self.full_clean()
        return super().save(*args, **kwargs)