"""Custom authentication backend allowing login with email."""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailBackend(ModelBackend):
    """Authenticate users by email address (instead of username)."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 'username' here is what the user typed in the email field
        email = kwargs.get('email') or username
        if email is None:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(email__iexact=email).order_by('id').first()
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
