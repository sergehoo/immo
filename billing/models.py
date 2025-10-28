from django.db import models


class RentInvoice(models.Model):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    STATUSES = [(PENDING, "En attente"), (PAID, "Payée"), (PARTIAL, "Partielle"), (OVERDUE, "En retard")]

    lease = models.ForeignKey("leasing.LeaseContract", on_delete=models.CASCADE, related_name="invoices")
    period = models.CharField(max_length=7)  # YYYY-MM
    amount_due = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="XOF")
    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING)
    due_date = models.DateField()
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("lease", "period")

    def __str__(self):
        return f"Facture {self.period} - {self.lease}"
