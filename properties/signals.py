# apps/listings/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Listing, Unit


def _sync_listing_geo(listing: Listing):
    prop = listing.unit.property
    listing.property_city = prop.city
    listing.property_district = prop.district


@receiver(pre_save, sender=Listing)
def listing_pre_save(sender, instance: Listing, **kwargs):
    if instance.unit_id and (not instance.property_city or not instance.property_district):
        _sync_listing_geo(instance)


@receiver(post_save, sender=Unit)
def unit_post_save(sender, instance: Unit, **kwargs):
    # Quand on modifie une Unit/Property, on propage dans toutes les Listings
    qs = instance.listings.all().select_related("unit__property")
    for listing in qs:
        _sync_listing_geo(listing)
        listing.save(update_fields=["property_city", "property_district"])
