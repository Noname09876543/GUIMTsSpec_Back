import uuid

from asgiref.sync import sync_to_async
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, authentication_classes, action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from app.forms import RequestForm
from app.models import ServiceRequest, Specialist
from django.db import connection

from app.permissions import IsAdmin
from app.serializers import *
from django.utils import timezone
import pytz
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import authentication_classes
from app import permissions
from django.conf import settings
import redis

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


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
            cls.instance = CustomUser.objects.get(username="admin")
        return cls.instance


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


class ServiceRequestListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        formed_at_from = request.query_params.get('formed_at_from')
        formed_at_to = request.query_params.get('formed_at_to')
        status = request.query_params.get('status')
        if request.user.is_staff:
            service_requests = ServiceRequest.objects.exclude(status="DELETED")
        else:
            service_requests = ServiceRequest.objects.filter(creator=request.user).exclude(status="DELETED")
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

    @method_permission_classes((IsAuthenticated,))
    def put(self, request, pk, format=None):
        service_request = self.get_object(pk)
        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes((IsAuthenticated,))
    def get(self, request, pk, format=None):
        service_request = self.get_object(pk)
        serializer = ServiceRequestSerializer(service_request)
        return Response(serializer.data)

    @method_permission_classes((IsAuthenticated,))
    def delete(self, request, pk, format=None):
        service_request = self.get_object(pk)
        service_request.status = "DELETED"
        service_request.save()
        serializer = ServiceRequestSerializer(service_request)
        return Response(serializer.data)
        # service_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['Put'])
@permission_classes([IsAuthenticated])
def form_service_request(request, pk, format=None):
    request_user = request.user
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
@permission_classes([IsAuthenticated])
def change_status(request, pk, format=None):
    if request.user.is_staff:
        request_user = request.user
        service_request = get_object_or_404(ServiceRequest, pk=pk)
        if request.data['status'] == "FINISHED" or request.data['status'] == "CANCELED":
            service_request.status = request.data['status']
            service_request.moderator = request_user
            if service_request.status == "FINISHED":
                service_request.finished_at = timezone.now()
            service_request.save()
            serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
            if serializer.is_valid():
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'error_message': "Неверный запрос, можно изменить статус заявки на FINISHED или CANCELED!"},
                status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error_message': "Статус заявки может поменять только пользователь с правами модератора!!"},
                        status=status.HTTP_403_FORBIDDEN)


class SpecialistListAPIView(APIView):
    permission_classes = []

    def get(self, request, format=None):
        creator = request.user
        if not creator.is_anonymous:
            service_request = ServiceRequest.objects.exclude(status="DELETED").filter(creator=creator).first()
        else:
            service_request = None
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

    @method_permission_classes((IsAdmin,))
    @swagger_auto_schema(request_body=SpecialistSerializer)
    def post(self, request, format=None):
        serializer = SpecialistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpecialistAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = []

    def get_object(self, pk):
        try:
            return Specialist.objects.get(pk=pk)
        except Specialist.DoesNotExist:
            raise Http404

    @method_permission_classes((IsAuthenticated,))
    def post(self, request, pk, format=None):
        specialist = get_object_or_404(Specialist, pk=pk)
        creator = request.user
        moderator = None
        print(request.user)
        service_request, created = ServiceRequest.objects.exclude(status="DELETED").get_or_create(creator=creator,
                                                                                                  moderator=moderator)
        service_request_specialist = ServiceRequestSpecialist.objects.get_or_create(specialist=specialist,
                                                                                    service_request=service_request)
        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @method_permission_classes((IsAdmin,))
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

    @method_permission_classes((IsAuthenticated,))
    def delete(self, request, pk, format=None):
        specialist = self.get_object(pk)
        creator = request.user
        service_request = ServiceRequest.objects.exclude(status="DELETED").filter(creator=creator).first()
        if service_request:
            service_request_specialist = ServiceRequestSpecialist.objects.get(specialist=specialist,
                                                                              service_request=service_request)
            service_request_specialist.delete()
            serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
            if serializer.is_valid():
                return Response(serializer.data)
        # specialist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@permission_classes([IsAdmin])
class deleteSpecialistAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]

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
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get(self, request, format=None):
        service_request_specialists = ServiceRequestSpecialist.objects.all()
        serializer = ServiceRequestSpecialistSerializer(service_request_specialists, many=True)

        return Response({'service_request_specialists': serializer.data})


class ServiceRequestSpecialistAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_object(self, pk):
        try:
            return ServiceRequestSpecialist.objects.get(pk=pk)
        except ServiceRequestSpecialist.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        service_request_specialist = self.get_object(pk)
        serializer = ServiceRequestSpecialistSerializer(service_request_specialist)
        return Response(serializer.data)

    @method_permission_classes(IsAuthenticated)
    def delete(self, request, pk, format=None):
        service_request_specialist = self.get_object(pk)
        service_request_specialist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    model_class = CustomUser

    def create(self, request):
        if self.model_class.objects.filter(username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            self.model_class.objects.create_user(username=serializer.data['username'],
                                                 email=serializer.data['email'],
                                                 full_name=serializer.data['full_name'],
                                                 password=serializer.data['password'],
                                                 phone=serializer.data['phone'],
                                                 is_superuser=serializer.data['is_superuser'],
                                                 is_staff=serializer.data['is_staff'])
            # is_superuser=False,
            # is_staff=False)
            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Error', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([AllowAny])
@authentication_classes([])
@csrf_exempt
@swagger_auto_schema(method='post', request_body=UserLoginSerializer)
@api_view(['Post'])
def login_view(request):
    username = request.POST["username"]
    password = request.POST["password"]
    # username = request.POST.get('username')
    # password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponse("{'status': 'ok'}")

        # random_key = uuid.uuid4()
        # session_storage.set(str(random_key), username)
        #
        # response = HttpResponse("{'status': 'ok'}")
        # response.set_cookie("session_id", random_key)

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")


@csrf_exempt
@api_view(['Post'])
def logout_view(request):
    # session_storage.delete(request.session.session_key)
    logout(request)

    # session_storage.delete(request.COOKIES.get('session_id'))
    # response.delete_cookie('session_id')
    return Response({'status': 'Success'})


from adrf.decorators import api_view as async_api_view
import asyncio
import time


@sync_to_async
def change_service_request(service_request_id):
    try:
        time.sleep(5)
        random_key = uuid.uuid4()
        service_request = ServiceRequest.objects.get(id=service_request_id)
        service_request.comment += f"\nТокен полученный при помощи асинхронного сервиса: {random_key}"
        service_request.save()
        return f"Токен {random_key} добавлен к заявке"
    except ServiceRequest.DoesNotExist:
        return "Нет заявки с указанным id!"


@async_api_view(['POST'])
async def async_task_view(request):
    service_request_id = request.POST["request_id"]
    # await asyncio.sleep(5)
    result = await asyncio.gather(change_service_request(service_request_id))
    return Response({'status': result})
