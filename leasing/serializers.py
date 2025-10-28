from rest_framework import serializers
from .models import LeaseContract

class LeaseContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseContract
        fields = "__all__"
