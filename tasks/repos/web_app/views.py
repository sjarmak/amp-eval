"""Views module with mixed concerns that need refactoring."""
import hashlib
import smtplib
from email.mime.text import MIMEText
from django.http import JsonResponse
from django.contrib.auth import authenticate
from .models import User
from .utils import get_user_profile


def login_view(request):
    """Login view with embedded auth logic that should be extracted."""
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    # This auth logic should be moved to separate auth module
    if not username or not password:
        return JsonResponse({'error': 'Missing credentials'}, status=400)
    
    # Hash password (this should be in auth service)
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    user = authenticate(username=username, password=password_hash)
    if user:
        return JsonResponse({'success': True, 'user_id': user.id})
    return JsonResponse({'error': 'Invalid credentials'}, status=401)


def register_view(request):
    """Registration with embedded email logic."""
    username = request.POST.get('username')
    email = request.POST.get('email')
    password = request.POST.get('password')
    
    # This email logic should be extracted to email service
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'User exists'}, status=400)
    
    user = User.objects.create(username=username, email=email, password=password)
    
    # Email sending logic (should be in separate service)
    msg = MIMEText(f'Welcome {username}! Your account has been created.')
    msg['Subject'] = 'Welcome to our app'
    msg['From'] = 'noreply@example.com'
    msg['To'] = email
    
    try:
        smtp = smtplib.SMTP('localhost', 587)
        smtp.send_message(msg)
        smtp.quit()
    except Exception:
        pass  # Ignore email errors for now
    
    return JsonResponse({'success': True, 'user_id': user.id})


def profile_view(request):
    """Profile view that depends on utils (creates circular import)."""
    user_id = request.GET.get('user_id')
    profile = get_user_profile(user_id)  # This creates circular import
    return JsonResponse(profile)
