from rest_framework.response import Response
from rest_framework import status
# from backend.serializers import ObjectSerializer
from server.backend import serializers
from drf_spectacular.utils import extend_schema_field


class ObjectSerializer(serializers.Serializer):
    uid = serializers.SerializerMethodField(read_only=True, allow_null=True)
    urn = serializers.SerializerMethodField(allow_null=True)

    value = serializers.SerializerMethodField('get_obj_value')

    @extend_schema_field(serializers.CharField(help_text='Unique identifier of object'))
    def get_uid(self, obj):
        uid_field = getattr(obj, 'UID_FIELD', None)
        if uid_field:
            return getattr(obj, uid_field, None)

    @extend_schema_field(serializers.CharField(help_text='Unique resource name of object'))
    def get_urn(self, obj):
        try:
            return getattr(obj, 'urn')
        except NotImplementedError:
            pass

    @extend_schema_field(serializers.CharField(help_text='String representation of object'))
    def get_obj_value(self, obj) -> str:
        return str(obj)


class CreateModelMixin:
    create_response_serializer_class = ObjectSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        data = self.create_response_serializer_class(
            instance=serializer.instance).data
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save()


class UpdateModelMixin:
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
