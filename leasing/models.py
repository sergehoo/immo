from django.db import models


class LeaseContract(models.Model):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    TYPES = [(RESIDENTIAL, "Résidentiel"), (COMMERCIAL, "Commercial")]

    unit = models.ForeignKey("properties.Unit", on_delete=models.PROTECT, related_name="leases")
    landlord = models.ForeignKey("parties.Party", on_delete=models.PROTECT, related_name="landlord_leases")
    tenant = models.ForeignKey("parties.Party", on_delete=models.PROTECT, related_name="tenant_leases")
    contract_type = models.CharField(max_length=16, choices=TYPES, default=RESIDENTIAL)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    monthly_rent = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="XOF")
    deposit_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bail {self.unit} - {self.tenant}"
