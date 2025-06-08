from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from StudentManagementSystem.models import SimpleAdmin

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        raw_password = request.POST.get('password')
        try:
            admin = SimpleAdmin.objects.get(username=username)
            if check_password(raw_password, admin.password):
                request.session['admin_id'] = admin.id
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'Invalid password.')
        except SimpleAdmin.DoesNotExist:
            messages.error(request, 'Admin user not found.')
    return render(request, 'admin/login.html')

def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')

def admin_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        raw_password = request.POST.get('password')
        if SimpleAdmin.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('admin_register')
        hashed_password = make_password(raw_password)
        SimpleAdmin.objects.create(username=username, password=hashed_password)
        messages.success(request, 'Registration successful. You can now log in.')
        return redirect('admin_login')
    return render(request, 'admin/register.html')
