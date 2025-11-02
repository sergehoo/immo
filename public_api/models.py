from django.db import models


# Create your models here.


class OrderedActiveModel(models.Model):
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ("order", "id")


class Banner(OrderedActiveModel):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    cta = models.CharField(max_length=64, default="Voir")
    to = models.CharField(max_length=200, default="/#listings")
    icon = models.CharField(max_length=64, blank=True)
    image = models.URLField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


class QuickAction(OrderedActiveModel):
    icon = models.CharField(max_length=64)
    label = models.CharField(max_length=80)
    to = models.CharField(max_length=200)
    gradient = models.BooleanField(default=False)
    color = models.CharField(max_length=16, blank=True)  # ex: #f97316


class Category(OrderedActiveModel):
    slug = models.SlugField(unique=True)  # "all", "rent", "sell", "featured", "new"
    label = models.CharField(max_length=80)
    icon = models.CharField(max_length=64, blank=True)
    color = models.CharField(max_length=16, blank=True)


class MapTeaser(OrderedActiveModel):
    image = models.URLField()
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    to = models.CharField(max_length=200, default="/#map")
