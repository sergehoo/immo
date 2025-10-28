from django.db import models

class MaintenanceTicket(models.Model):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"
    STATUSES = [(OPEN, "Ouvert"), (IN_PROGRESS, "En cours"), (DONE, "Clôturé"), (CANCELLED, "Annulé")]

    unit = models.ForeignKey("properties.Unit", on_delete=models.CASCADE, related_name="tickets")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUSES, default=OPEN)
    cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_by = models.ForeignKey("parties.Party", on_delete=models.SET_NULL, null=True, blank=True, related_name="created_tickets")
    assigned_to = models.ForeignKey("parties.Party", on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
