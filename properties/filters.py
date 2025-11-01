# properties/filters.py
import django_filters
from django.db import models

from .models import Listing


class ListingFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method="filter_search")
    type = django_filters.CharFilter(field_name="listing_type")
    is_featured = django_filters.BooleanFilter()

    class Meta:
        model = Listing
        fields = ("listing_type", "is_featured")

    def filter_search(self, qs, name, value):
        # cherche dans titre bien, adresse, ville…
        return qs.filter(
            models.Q(unit__property__title__icontains=value) |
            models.Q(unit__property__city__icontains=value) |
            models.Q(description__icontains=value)
        )
