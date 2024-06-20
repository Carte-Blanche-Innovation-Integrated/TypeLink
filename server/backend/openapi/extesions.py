from drf_spectacular.contrib.rest_polymorphic import (
    PolymorphicSerializerExtension as PolymorphicSerializerExtensionBase,
)
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import ResolvedComponent, is_patched_serializer, build_object_type, build_basic_type
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.types import OpenApiTypes
from server.backend import serializers


class PolymorphicSerializer(serializers.Serializer):
    discriminator_field = 'type'

    serializer_mapping = {}

    def get_serializer_class(self, discriminator: str) -> type[serializers.Serializer]:
        return self.serializer_mapping[discriminator]

    def get_serializer(self, discriminator: str, **kwargs) -> serializers.Serializer:
        serializer_class = self.get_serializer_class(discriminator)
        kwargs['context'] = self.context
        return serializer_class(**kwargs)

    def get_fields(self):
        return {
            self.discriminator_field: serializers.CharField(),
        }

    def get_discriminator(self, instance) -> str:
        raise NotImplementedError()

    def to_representation(self, value):
        discriminator = self.get_discriminator(value)
        serialized = self.get_serializer(
            discriminator, instance=value).to_representation(value)
        serialized[self.discriminator_field] = discriminator
        return serialized

    def to_internal_value(self, data):
        discriminator = super().to_internal_value(data)[
            self.discriminator_field]

        serializer = self.get_serializer(discriminator, data=data).data
        setattr(self, '_serializer', serializer)

        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def save(self, **kwargs):
        assert hasattr(
            self, '_errors'), 'You must call `.is_valid()` before calling `.save()`.'

        assert not self.errors, 'You cannot call `.save()` on a serializer with invalid data.'

        assert not hasattr(self, '_data'), (
            "You cannot call `.save()` after accessing `serializer.data`."
            "If you need to access data before committing to the database then "
            "inspect 'serializer.validated_data' instead. "
        )

        return getattr(self, '_serializer').save(**kwargs)


class UserAccessTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    name = 'bearerAuth'
    target_class = 'splinter.authentication.UserAccessTokenAuthentication'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'http',
            'scheme': 'bearer',
            'description': 'User access token',
            'bearerFormat': 'JWT',
        }


class PolymorphicSerializerExtension(PolymorphicSerializerExtensionBase):
    target_class = f'{PolymorphicSerializer.__module__}.{
        PolymorphicSerializer.__name__}'

    def build_typed_component(self, auto_schema, component, resource_type_field_name, patched, discriminator=None):
        if spectacular_settings.COMPONENT_SPLIT_REQUEST and component.name.endswith('Request'):
            typed_component_name = component.name[:-
                                                  len('Request')] + 'TypedRequest'
        else:
            typed_component_name = f'{component.name}Typed'

        resource_type_schema = build_object_type(
            properties={resource_type_field_name: {
                **build_basic_type(OpenApiTypes.STR),
                # adds support for typescript discriminated union
                "enum": [discriminator]
            }},
            required=None if patched else [resource_type_field_name]
        )
        # if sub-serializer has an empty schema, only expose the resource_type field part
        if component.schema:
            schema = {'allOf': [resource_type_schema, component.ref]}
        else:
            schema = resource_type_schema

        component_typed = ResolvedComponent(
            name=typed_component_name,
            type=ResolvedComponent.SCHEMA,
            object=component.object,
            schema=schema,
        )
        auto_schema.registry.register_on_missing(component_typed)
        return component_typed

    def map_serializer(self, auto_schema, direction):
        sub_components = {}
        serializer: PolymorphicSerializer = self.target

        for discriminator, sub_serializer in serializer.serializer_mapping.items():
            sub_serializer.partial = serializer.partial
            component = auto_schema.resolve_serializer(
                sub_serializer, direction)
            if not component:
                # rebuild a virtual schema-less component to model empty serializers
                component = ResolvedComponent(
                    name=auto_schema._get_serializer_name(
                        sub_serializer, direction),
                    type=ResolvedComponent.SCHEMA,
                    object='virtual',
                )
            typed_component = self.build_typed_component(
                auto_schema=auto_schema,
                component=component,
                resource_type_field_name=serializer.discriminator_field,
                patched=is_patched_serializer(sub_serializer, direction),
                discriminator=discriminator,
            )
            print(typed_component)
            sub_components[discriminator] = typed_component.ref

        return {
            'oneOf': list(sub_components.values()),
            'discriminator': {
                'propertyName': serializer.discriminator_field,
                'mapping': {discriminator: ref['$ref'] for discriminator, ref in sub_components.items()},
            },
        }
