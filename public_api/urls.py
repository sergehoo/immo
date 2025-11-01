from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from accounts.views import AddressViewSet, CompanyViewSet, CompanyMembershipViewSet, KYCDocumentViewSet, RegisterView, \
    MeView, MyProfileView
from billing.views import RentInvoiceViewSet
from leasing.views import LeaseContractViewSet
from maintenance.views import MaintenanceTicketViewSet
from public_api.views import PartyViewSet, UnitViewSet, ListingViewSet, FavoriteListingViewSet, VisitRequestViewSet, \
    AmenityViewSet, ValuationViewSet, HomeView, SummaryView, SearchSuggestView
from public_api.views import PropertyViewSet

router = DefaultRouter()

router.register(r"addresses", AddressViewSet, basename="address")
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"memberships", CompanyMembershipViewSet, basename="membership")
router.register(r"kyc-docs", KYCDocumentViewSet, basename="kyc")

router.register(r"parties", PartyViewSet, basename="party")

router.register(r"leases", LeaseContractViewSet, basename="leasecontract")
router.register(r"invoices", RentInvoiceViewSet, basename="invoice")
# router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"tickets", MaintenanceTicketViewSet, basename="maintenanceticket")
# Parties (lecture seule, pour autocomplete/interne)


# Properties
router.register(r"properties", PropertyViewSet, basename="property")
router.register(r"units", UnitViewSet, basename="unit")

# Listings public
router.register(r"listings", ListingViewSet, basename="listing")

# Favoris & Visites (user)
router.register(r"favorites", FavoriteListingViewSet, basename="favorite")
router.register(r"visit-requests", VisitRequestViewSet, basename="visitrequest")

# Catalogue / Staff
router.register(r"amenities", AmenityViewSet, basename="amenity")
router.register(r"valuations", ValuationViewSet, basename="valuation")

urlpatterns = [
                  path("", include(router.urls)),
                  # Auth JWT
                  path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
                  path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
                  path("auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
                  # Register + Me + Profile
                  path("auth/signup/", RegisterView.as_view(), name="register"),
                  path("auth/me/", MeView.as_view(), name="me"),
                  path("auth/profile/", MyProfileView.as_view(), name="my_profile"),

                  path('home/', HomeView.as_view(), name='home'),
                  path('summary/', SummaryView.as_view(), name='summary'),
                  path('search/suggest/', SearchSuggestView.as_view(), name='search-suggest'),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
