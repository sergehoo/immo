# properties/management/commands/seed_properties.py
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from faker import Faker
import random

from properties.models import (
    Property, Unit, Listing, Amenity,
    PropertyAmenity, UnitAmenity
)
from accounts.models import User  # si tu as une app accounts
from parties.models import Party  # optionnel si déjà présent

fake = Faker("fr_FR")


class Command(BaseCommand):
    help = "Génère des données factices pour les modèles Property, Unit, Listing, etc."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=10, help="Nombre de propriétés à générer")

    def handle(self, *args, **options):
        count = options["count"]

        self.stdout.write(self.style.WARNING(f"Génération de {count} propriétés avec unités et annonces..."))

        users = list(User.objects.all()[:10])
        if not users:
            self.stdout.write(self.style.ERROR("Aucun utilisateur trouvé. Crée d’abord au moins un utilisateur."))
            return

        # Création de quelques amenities s’ils n’existent pas
        amenity_labels = ["Piscine", "Garage", "Jardin", "Sécurité 24/7", "Ascenseur", "Balcon", "Climatisation"]
        for label in amenity_labels:
            Amenity.objects.get_or_create(code=label.lower().replace(" ", "-"), label=label)

        amenities = list(Amenity.objects.all())

        for i in range(count):
            owner_user = random.choice(users)
            prop = Property.objects.create(
                title=fake.sentence(nb_words=4),
                property_type=random.choice([Property.RESIDENTIAL, Property.COMMERCIAL, Property.LAND]),
                address=fake.street_address(),
                city=fake.city(),
                country="Côte d'Ivoire",
                owner_user=owner_user,
                geom=Point(float(fake.longitude()), float(fake.latitude()))
            )

            # Units
            for j in range(random.randint(1, 4)):
                unit = Unit.objects.create(
                    property=prop,
                    name=f"Unité {j + 1}",
                    bedrooms=random.randint(1, 5),
                    bathrooms=random.randint(1, 3),
                    size_m2=random.uniform(30, 250),
                    is_available=True
                )

                # Listings
                listing_type = random.choice([Listing.RENT, Listing.SALE])
                Listing.objects.create(
                    unit=unit,
                    listing_type=listing_type,
                    price=random.randint(100_000, 10_000_000),
                    description=fake.text(150),
                    currency="XOF",
                    is_active=True,
                    is_featured=random.choice([True, False]),
                    available_from=timezone.now().date(),
                )

                # Unit amenities aléatoires
                for amenity in random.sample(amenities, random.randint(1, 3)):
                    UnitAmenity.objects.get_or_create(unit=unit, amenity=amenity)

            # Property amenities aléatoires
            for amenity in random.sample(amenities, random.randint(2, 4)):
                PropertyAmenity.objects.get_or_create(property=prop, amenity=amenity)

        self.stdout.write(self.style.SUCCESS(f"{count} propriétés créées avec succès !"))
