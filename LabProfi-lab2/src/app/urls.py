"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.views import home_page, requests_list, send_request, service_page, services_list_page

urlpatterns = [
    path('adminer/', admin.site.urls),
    path('users/', include('auth_users.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path('', home_page, name="home"),
    path('services/', services_list_page, name="service_select"),
    path('services/<int:id>/', service_page, name="service_info"),
    path('services/<int:id>/request', send_request, name="send_request"),
    path('requests/', requests_list, name="requests_list"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
