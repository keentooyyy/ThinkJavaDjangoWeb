"""
URL configuration for ThinkJava project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from django.urls import path, include

from StudentManagementSystem.views.export_rankings import export_ranking_xls, print_ranking
from StudentManagementSystem.views.ph_locations import provinces, cities, barangays

urlpatterns = [
    #    path('admin/', admin.site.urls),
    path('api/', include('GameProgress.urls')),
    path('', include('StudentManagementSystem.urls.admin')),
    path('teacher/', include('StudentManagementSystem.urls.teacher')),
    path('student/', include('StudentManagementSystem.urls.student')),
    path("provinces/", provinces),
    path("cities/", cities),
    path("barangays/", barangays),
    path("ranking/export-xls/", export_ranking_xls, name="export_ranking_xls"),
    path("ranking/print/", print_ranking, name="print_ranking"),
]
