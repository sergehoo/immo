from rest_framework import serializers
from .models import RentInvoice


class RentInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentInvoice
        fields = "__all__"
