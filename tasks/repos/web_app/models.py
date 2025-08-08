"""User models with business logic that should be in services."""
from django.db import models
from .utils import format_username  # Creates circular import


class User(models.Model):
    """User model with embedded business logic."""
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    password = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        # This formatting logic should be in a service
        self.username = format_username(self.username)  # Circular import
        super().save(*args, **kwargs)
    
    def send_welcome_email(self):
        """This method should be in email service."""
        # Email logic embedded in model (bad practice)
        from .views import register_view  # Another circular import
        pass
    
    def get_profile_data(self):
        """Business logic that should be in service layer."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'member_since': self.created_at.strftime('%Y-%m-%d'),
            'status': 'active' if self.is_active else 'inactive'
        }
