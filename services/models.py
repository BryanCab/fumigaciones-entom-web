from django.db import models
from django.core.validators import MinValueValidator
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# --------------------------------------------------------------------------------------
# Helper reutilizable para slugs únicos (idéntico al que usas en products)
def _generate_unique_slug(instance, base_value, slug_field_name="slug"):
    slug_field = instance._meta.get_field(slug_field_name)
    max_length = slug_field.max_length

    base_slug = slugify(base_value or "")
    if not base_slug:
        base_slug = "item"

    base_slug = base_slug[:max_length]

    ModelClass = instance.__class__
    qs = ModelClass._default_manager.all()
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)

    if not qs.filter(**{slug_field_name: base_slug}).exists():
        return base_slug

    suffix = 2
    while True:
        candidate = f"{base_slug[: max_length - (len(str(suffix)) + 1)]}-{suffix}"
        if not qs.filter(**{slug_field_name: candidate}).exists():
            return candidate
        suffix += 1


# --------------------------------------------------------------------------------------
class Service(models.Model):

    # ------------------------------------------------------------------
    # CHOICES
    # ------------------------------------------------------------------
    SERVICE_TYPES = [
        ("PREVENTIVO", "Preventivo"),
        ("CORRECTIVO", "Correctivo"),
    ]

    METHODS = [
        ("AM", "Asperción manual"),
        ("AMO", "Asperción motorizada"),
        ("INYECCION", "Inyección"),
        ("NEBULIZACION", "Nebulización"),
        ("TERMO", "Termonebulización"),
        ("APLMAN", "Aplicación manual"),
        ("ESPUMA", "Espuma"),
        ("ESPOLVO", "Espolvoreo"),
    ]

    # ------------------------------------------------------------------
    # Guardamos el slug original para detectar cambios ilegales
    # ------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_slug = self.slug

    # ------------------------------------------------------------------
    # CAMPOS PRINCIPALES
    # ------------------------------------------------------------------
    name = models.CharField(
        max_length=200,
        unique=True,
        error_messages={
            "unique": "Ya existe un servicio con ese nombre.",
        },
        verbose_name="Nombre del servicio",
    )

    slug = models.SlugField(
        max_length=150,
        unique=True,
        blank=True,
        db_index=True,
        verbose_name="Slug",
    )

    description = models.TextField(verbose_name="Descripción")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Precio",
    )

    image = models.ImageField(
        upload_to="services/",
        verbose_name="Imagen del servicio",
    )

    # ------------------------------------------------------------------
    # CAMPOS ESPECIALES
    # ------------------------------------------------------------------
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        verbose_name="Tipo de servicio",
    )

    method = models.CharField(
        max_length=20,
        choices=METHODS,
        verbose_name="Método aplicado",
    )

    estimated_time = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Tiempo estimado",
    )

    materials_description = models.TextField(
        blank=True,
        verbose_name="Materiales utilizados",
    )

    benefits = models.TextField(
        blank=True,
        verbose_name="Beneficios",
    )

    recommended_for = models.TextField(
        blank=True,
        verbose_name="Recomendado para",
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    # ------------------------------------------------------------------
    # Métodos
    # ------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse("services:service_detail", kwargs={"slug": self.slug})

    def clean(self):
        """Validaciones de negocio específicas del modelo Service."""
        errors = {}

        # Slug inmutable
        if self.pk and self._original_slug and self.slug != self._original_slug:
            errors["slug"] = (
                "El slug es inmutable. Si necesitas cambiar la URL, usa un redireccionamiento 301."
            )

        # Validar descripción mínima (ejemplo)
        if self.description and len(self.description) < 10:
            errors["description"] = "La descripción es demasiado corta."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Crear slug si no existe
        if not self.pk and not self.slug:
            self.slug = _generate_unique_slug(self, self.name, slug_field_name="slug")

        # Ejecutar clean() + validaciones de campo + unique
        self.full_clean()

        super().save(*args, **kwargs)
        self._original_slug = self.slug  # actualizar slug original

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
