# core/models.py

from django.db import models
from django.contrib.auth.models import User # Assuming you have a User model for your project
from django.utils import timezone

# --- ADD THIS IMPORT ---
from solar.models import Cliente # Import your Cliente model from the 'solar' app
# --- END ADD IMPORT ---

class SiteProject(models.Model):
    # ... your existing fields ...
    user = models.ForeignKey(User, on_delete=models.CASCADE) # Assuming SiteProject is linked to a user
    name = models.CharField(max_length=255, default="Novo Site")
    base_html_code = models.TextField()
    content_data = models.JSONField(default=dict) # Ensure this is present for content storage
    final_html_code = models.TextField(blank=True, null=True)
    published_url = models.URLField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # This is the line causing the NameError if Cliente isn't imported
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='site_projects') 

    class Meta:
        # Add any meta options here, e.g., ordering
        ordering = ['-created_at']

    def __str__(self):
        return self.name