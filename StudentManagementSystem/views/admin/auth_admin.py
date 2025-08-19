from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect

from StudentManagementSystem.models import SimpleAdmin


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
        return redirect('unified_login')
    return render(request, 'admin/register.html')
