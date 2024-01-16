from rest_framework import serializers

from app.models import *


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'full_name', 'email', 'phone', 'password', 'is_staff', 'is_superuser']
        # fields = ['username', 'full_name', 'email', 'phone', 'password']


class SpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialist
        fields = ("id", "name", "desc", "preview_image")

    # def update(self, instance, validated_data):
    #     instance = super(SpecialistSerializer, self).update(instance, validated_data)
    #     # service_requests = validated_data.pop('service_request')
    #     return instance


class ServiceRequestSpecialistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequestSpecialist
        fields = "__all__"


class ServiceRequestSerializer(serializers.ModelSerializer):
    # creator = UserSerializer()
    # moderator = UserSerializer()
    creator = serializers.CharField(source="creator.username", read_only=True)
    moderator = serializers.CharField(source="moderator.username", read_only=True)
    specialist = SpecialistSerializer(many=True)

    class Meta:
        model = ServiceRequest
        fields = "__all__"
