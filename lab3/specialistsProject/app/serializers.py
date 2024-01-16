from rest_framework import serializers

from app.models import *


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = "__all__"


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
