"""Base schema and shared reference types."""

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        use_enum_values=True,
        populate_by_name=True,
        extra="forbid",
    )


class ParameterReference(BaseSchema):
    """Reference to an optimizable parameter."""

    param: str = Field(..., alias="$param")


class Reference(BaseSchema):
    """Reference to a reusable component."""

    ref: str = Field(..., alias="$ref")
