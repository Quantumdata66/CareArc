"""Base Pydantic Schema with Automated CamelCase Aliasing."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Base schema for all CareArc DTOs.

    Features:
    - Automatically converts Python snake_case field names to camelCase for API JSON serialization.
    - Enables population by field name (accepts both snake_case and camelCase input).
    - Enables ORM mode (from_attributes = True) for direct SQLAlchemy object conversion.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
