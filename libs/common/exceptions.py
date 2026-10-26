"""Domain-specific typed exception hierarchy for the accident prediction platform."""


class AccidentPlatformError(Exception):
    """Base exception for all domain errors within the accident prediction platform."""
    pass


class ConfigurationError(AccidentPlatformError):
    """Raised when configuration files or environment variables are missing or invalid."""
    pass


class ProviderError(AccidentPlatformError):
    """Base exception for external upstream provider failures."""
    pass


class WeatherProviderError(ProviderError):
    """Raised when NOAA or Open-Meteo weather APIs fail or timeout."""
    pass


class TrafficProviderError(ProviderError):
    """Raised when State 511 or DOT traffic feeds fail or return invalid payload."""
    pass


class RoutingEngineError(ProviderError):
    """Raised when Valhalla or OSRM route calculations fail."""
    pass


class SpatialIndexingError(AccidentPlatformError):
    """Raised when H3 indexing or coordinate projection operations fail."""
    pass


class GraphStoreError(AccidentPlatformError):
    """Raised when PostGIS or GeoPackage road network queries fail."""
    pass


class ModelInferenceError(AccidentPlatformError):
    """Raised when ONNX Runtime or PyTorch model inference fails."""
    pass


class ExplainabilityError(AccidentPlatformError):
    """Raised when localized micro decision tree mining fails."""
    pass


class FeatureCacheError(AccidentPlatformError):
    """Raised when Redis or in-memory feature cache operations fail."""
    pass
