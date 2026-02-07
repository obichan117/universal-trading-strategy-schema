"""Integration tests for UTSS schema-engine capability sync.

Validates that pyutss implements all capabilities defined in the UTSS schema.
Uses strict subset assertions — if the schema adds a new capability and the
engine doesn't implement it, these tests fail immediately.
"""

from utss.capabilities import (
    SCHEMA_VERSION,
    SUPPORTED_ACTION_TYPES,
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_INDICATORS,
    SUPPORTED_SIGNAL_TYPES,
    SUPPORTED_SIZING_TYPES,
    SUPPORTED_UNIVERSE_TYPES,
)
from pyutss.engine.capabilities import (
    DEFERRED_SIGNAL_TYPES,
    IMPLEMENTED_ACTION_TYPES,
    IMPLEMENTED_CONDITION_TYPES,
    IMPLEMENTED_INDICATORS,
    IMPLEMENTED_SIGNAL_TYPES,
    IMPLEMENTED_SIZING_TYPES,
    IMPLEMENTED_UNIVERSE_TYPES,
)


class TestSchemaVersion:
    """Tests for schema version compatibility."""

    def test_schema_version_defined(self):
        """Schema version should be defined."""
        assert SCHEMA_VERSION is not None
        assert SCHEMA_VERSION == "1.0.0"


class TestIndicatorSync:
    """Every schema-defined indicator must be in the engine registry."""

    def test_all_schema_indicators_implemented(self):
        schema_set = set(SUPPORTED_INDICATORS)
        missing = schema_set - IMPLEMENTED_INDICATORS
        assert not missing, (
            f"Schema defines indicators not in engine registry: {sorted(missing)}"
        )


class TestConditionTypeSync:
    """Every schema-defined condition type must be implemented."""

    def test_all_condition_types_implemented(self):
        schema_set = set(SUPPORTED_CONDITION_TYPES)
        missing = schema_set - IMPLEMENTED_CONDITION_TYPES
        assert not missing, (
            f"Schema defines condition types not implemented: {sorted(missing)}"
        )


class TestSignalTypeSync:
    """Every schema-defined signal type must be implemented or explicitly deferred."""

    def test_all_signal_types_accounted_for(self):
        schema_set = set(SUPPORTED_SIGNAL_TYPES)
        accounted = IMPLEMENTED_SIGNAL_TYPES | DEFERRED_SIGNAL_TYPES
        missing = schema_set - accounted
        assert not missing, (
            f"Schema defines signal types neither implemented nor deferred: {sorted(missing)}. "
            "Add to IMPLEMENTED_SIGNAL_TYPES or DEFERRED_SIGNAL_TYPES."
        )

    def test_deferred_signals_are_valid_schema_types(self):
        """Deferred set should only contain types the schema actually defines."""
        schema_set = set(SUPPORTED_SIGNAL_TYPES)
        stale = DEFERRED_SIGNAL_TYPES - schema_set
        assert not stale, (
            f"DEFERRED_SIGNAL_TYPES contains types not in schema: {sorted(stale)}"
        )


class TestSizingTypeSync:
    """Every schema-defined sizing type must be implemented."""

    def test_all_sizing_types_implemented(self):
        schema_set = set(SUPPORTED_SIZING_TYPES)
        missing = schema_set - IMPLEMENTED_SIZING_TYPES
        assert not missing, (
            f"Schema defines sizing types not implemented: {sorted(missing)}"
        )


class TestActionTypeSync:
    """Every schema-defined action type must be implemented."""

    def test_all_action_types_implemented(self):
        schema_set = set(SUPPORTED_ACTION_TYPES)
        missing = schema_set - IMPLEMENTED_ACTION_TYPES
        assert not missing, (
            f"Schema defines action types not implemented: {sorted(missing)}"
        )


class TestUniverseTypeSync:
    """Every schema-defined universe type must be implemented."""

    def test_all_universe_types_implemented(self):
        schema_set = set(SUPPORTED_UNIVERSE_TYPES)
        missing = schema_set - IMPLEMENTED_UNIVERSE_TYPES
        assert not missing, (
            f"Schema defines universe types not implemented: {sorted(missing)}"
        )
