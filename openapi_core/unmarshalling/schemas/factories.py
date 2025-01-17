import sys
import warnings
from typing import Optional

from openapi_core.spec import Spec
from openapi_core.unmarshalling.schemas.datatypes import (
    FormatUnmarshallersDict,
)
from openapi_core.unmarshalling.schemas.exceptions import (
    FormatterNotFoundError,
)
from openapi_core.unmarshalling.schemas.unmarshallers import (
    FormatsUnmarshaller,
)
from openapi_core.unmarshalling.schemas.unmarshallers import SchemaUnmarshaller
from openapi_core.unmarshalling.schemas.unmarshallers import TypesUnmarshaller
from openapi_core.validation.schemas.datatypes import CustomFormattersDict
from openapi_core.validation.schemas.datatypes import FormatValidatorsDict
from openapi_core.validation.schemas.factories import SchemaValidatorsFactory


class SchemaUnmarshallersFactory:
    def __init__(
        self,
        schema_validators_factory: SchemaValidatorsFactory,
        types_unmarshaller: TypesUnmarshaller,
        format_unmarshallers: Optional[FormatUnmarshallersDict] = None,
        custom_formatters: Optional[CustomFormattersDict] = None,
    ):
        self.schema_validators_factory = schema_validators_factory
        self.types_unmarshaller = types_unmarshaller
        if format_unmarshallers is None:
            format_unmarshallers = {}
        self.format_unmarshallers = format_unmarshallers
        if custom_formatters is None:
            custom_formatters = {}
        else:
            warnings.warn(
                "custom_formatters is deprecated. "
                "Use extra_format_validators to validate custom formats "
                "and use extra_format_unmarshallers to unmarshal custom formats.",
                DeprecationWarning,
            )
        self.custom_formatters = custom_formatters

    def create(
        self,
        schema: Spec,
        format_validators: Optional[FormatValidatorsDict] = None,
        format_unmarshallers: Optional[FormatUnmarshallersDict] = None,
        extra_format_validators: Optional[FormatValidatorsDict] = None,
        extra_format_unmarshallers: Optional[FormatUnmarshallersDict] = None,
    ) -> SchemaUnmarshaller:
        """Create unmarshaller from the schema."""
        if schema is None:
            raise TypeError("Invalid schema")

        if schema.getkey("deprecated", False):
            warnings.warn("The schema is deprecated", DeprecationWarning)

        if extra_format_validators is None:
            extra_format_validators = {}
        extra_format_validators.update(
            {
                name: formatter.validate
                for name, formatter in self.custom_formatters.items()
            }
        )
        schema_validator = self.schema_validators_factory.create(
            schema,
            format_validators=format_validators,
            extra_format_validators=extra_format_validators,
        )

        schema_format = schema.getkey("format")

        formats_unmarshaller = FormatsUnmarshaller(
            format_unmarshallers or self.format_unmarshallers,
            extra_format_unmarshallers,
            self.custom_formatters,
        )

        # FIXME: don;t raise exception on unknown format
        # See https://github.com/python-openapi/openapi-core/issues/515
        if (
            schema_format
            and schema_format not in schema_validator
            and schema_format not in formats_unmarshaller
        ):
            raise FormatterNotFoundError(schema_format)

        return SchemaUnmarshaller(
            schema,
            schema_validator,
            self.types_unmarshaller,
            formats_unmarshaller,
        )
