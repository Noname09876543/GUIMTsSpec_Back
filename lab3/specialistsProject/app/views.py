from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from app.forms import RequestForm
from app.models import ServiceRequest, Specialist
from django.db import connection

from app.serializers import *
from django.utils import timezone
import pytz


def home_page(request):
    return render(request, "home.html")


def services_list_page(request):
    if request.method == "POST":
        specialist_id = request.POST.get("specialist")
        with connection.cursor() as cursor:
            cursor.execute(f"UPDATE app_specialist SET is_active = 'FALSE' WHERE id = {specialist_id}")

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
    last_requests = ServiceRequest.objects.raw(
        f'SELECT * FROM app_servicerequest WHERE user_id = {request.user.id} ORDER BY created_at DESC LIMIT 2')
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


class SingletonUser(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = User.objects.get(username="admin")
        return cls.instance


class ServiceRequestListAPIView(APIView):
    def get(self, request, format=None):
        formed_at_from = request.query_params.get('formed_at_from')
        formed_at_to = request.query_params.get('formed_at_to')
        status = request.query_params.get('status')
        service_requests = ServiceRequest.objects.exclude(status="DELETED")
        if status is not None:
            service_requests = service_requests.filter(status=status)
        # if created_at_from is not None and created_at_to is not None:
        if formed_at_from is not None:
            service_requests = service_requests.filter(formed_at__date__gte=formed_at_from)
        if formed_at_to is not None:
            service_requests = service_requests.filter(formed_at__date__lte=formed_at_to)
        serializer = ServiceRequestSerializer(service_requests, many=True)
        return Response({'service_requests': serializer.data})


class ServiceRequestAPIView(APIView):
    def get_object(self, pk):
        try:
            return ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            raise Http404

    def put(self, request, pk, format=None):
        service_request = self.get_object(pk)
        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk, format=None):
        service_request = self.get_object(pk)
        serializer = ServiceRequestSerializer(service_request)
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        service_request = self.get_object(pk)
        service_request.status = "DELETED"
        service_request.save()
        serializer = ServiceRequestSerializer(service_request)
        return Response(serializer.data)
        # service_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['Put'])
def form_service_request(request, pk, format=None):
    request_user = SingletonUser()
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request_user == service_request.creator:
        service_request.status = "IN_WORK"
        service_request.formed_at = timezone.now()
        service_request.save()
        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error_message': "У вас нет прав для изменения статуса заявки!"},
                        status=status.HTTP_400_BAD_REQUEST)


@api_view(['Put'])
def change_status(request, pk, format=None):
    request_user = SingletonUser()
    service_request = get_object_or_404(ServiceRequest, pk=pk)
    if request_user == service_request.moderator:
        service_request.status = request.data['status']
        if service_request.status == "FINISHED":
            service_request.finished_at = timezone.now()
        service_request.save()
        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error_message': "У вас нет прав для изменения статуса заявки!"},
                        status=status.HTTP_400_BAD_REQUEST)


class SpecialistListAPIView(APIView):
    def get(self, request, format=None):
        # is_active = request.query_params.get('is_active')
        creator = SingletonUser()
        moderator = SingletonUser()
        service_request = ServiceRequest.objects.exclude(status="DELETED").filter(creator=creator,
                                                                                  moderator=moderator).first()
        specialists = Specialist.objects.filter(is_active=True)
        name = request.query_params.get('name')
        if name:
            specialists = specialists.filter(name__contains=name)

        # if is_active == "true":
        #     specialists = specialists.filter(is_active=True)
        # if is_active == "false":
        #     specialists = specialists.filter(is_active=False)
        serializer = SpecialistSerializer(specialists, many=True)
        if service_request:
            service_request_id = service_request.id
        else:
            service_request_id = None
        return Response({"service_request_id": service_request_id, 'specialists': serializer.data})

    def post(self, request, format=None):
        serializer = SpecialistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpecialistAPIView(APIView):

    def get_object(self, pk):
        try:
            return Specialist.objects.get(pk=pk)
        except Specialist.DoesNotExist:
            raise Http404

    def post(self, request, pk, format=None):
        specialist = get_object_or_404(Specialist, pk=pk)
        creator = SingletonUser()
        moderator = SingletonUser()
        service_request, created = ServiceRequest.objects.exclude(status="DELETED").get_or_create(creator=creator,
                                                                                                  moderator=moderator)
        service_request_specialist = ServiceRequestSpecialist.objects.get_or_create(specialist=specialist,
                                                                                    service_request=service_request)
        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        specialist = self.get_object(pk)
        serializer = SpecialistSerializer(specialist, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk, format=None):
        specialist = self.get_object(pk)
        serializer = SpecialistSerializer(specialist)
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        specialist = self.get_object(pk)
        creator = SingletonUser()
        moderator = SingletonUser()
        service_request = ServiceRequest.objects.exclude(status="DELETED").filter(creator=creator,
                                                                                  moderator=moderator).first()
        if service_request:
            service_request_specialist = ServiceRequestSpecialist.objects.get(specialist=specialist,
                                                                              service_request=service_request)
            service_request_specialist.delete()
            serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
            if serializer.is_valid():
                return Response(serializer.data)
        # specialist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class deleteSpecialistAPIView(APIView):
    def get_object(self, pk):
        try:
            return Specialist.objects.get(pk=pk)
        except Specialist.DoesNotExist:
            raise Http404

    def delete(self, request, pk, format=None):
        specialist = self.get_object(pk)
        specialist.is_active = False
        specialist.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceRequestSpecialistListAPIView(APIView):
    def get(self, request, format=None):
        service_request_specialists = ServiceRequestSpecialist.objects.all()
        serializer = ServiceRequestSpecialistSerializer(service_request_specialists, many=True)

        return Response({'service_request_specialists': serializer.data})


class ServiceRequestSpecialistAPIView(APIView):
    def get_object(self, pk):
        try:
            return ServiceRequestSpecialist.objects.get(pk=pk)
        except ServiceRequestSpecialist.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        service_request_specialist = self.get_object(pk)
        serializer = ServiceRequestSpecialistSerializer(service_request_specialist)
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        service_request_specialist = self.get_object(pk)
        service_request_specialist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
