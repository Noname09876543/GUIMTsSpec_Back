from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from app.forms import RequestForm
from app.models import ServiceRequest, Specialist
from django.db import connection


def home_page(request):
    return render(request, "home.html")


def services_list_page(request):
    query = request.GET.get("q")
    if query:
        specialists = Specialist.objects.filter(name__icontains=query, is_active=True)
    else:
        specialists = Specialist.objects.filter(is_active=True)

    return render(request, "service_select.html", {"specialists": specialists, "query": query})


def service_page(request, id):
    specialist = Specialist.objects.get(pk=id)
    request_form = RequestForm()
    return render(request, "service_info.html", {"specialist": specialist, "request_form": request_form})


@login_required
def requests_list(request):

    if request.method == "POST":
        request_id = request.POST.get("request")
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE app_servicerequest SET status = 'CANCELED' WHERE id = {request_id}")
        # service_request = ServiceRequest.objects.get(id=request_id)
        # service_request.status = ServiceRequest.STATUS_CHOICES[2][1]
        # service_request.save()
    requests = ServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    last_requests = ServiceRequest.objects.raw(f'SELECT * FROM app_servicerequest WHERE user_id = {request.user.id} ORDER BY created_at DESC LIMIT 2')
    return render(request, "requests_list.html", {"requests": requests, "last_requests": last_requests})


@login_required
def send_request(request, id):
    form = RequestForm(request.POST)
    if form.is_valid():
        service_request = ServiceRequest(user=request.user, comment=form.cleaned_data["comment"])
        service_request.save()
        service_request.specialist.add(id, id)
        service_request.save()
    return redirect(reverse('requests_list'))
