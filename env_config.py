"""
env_config.py
A comprehensive environment variable configuration management module
"""

import os
import json
import yaml
from typing import Optional, Dict, Any, List, Union, Type, TypeVar, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import re
from functools import lru_cache
import logging
from dotenv import load_dotenv, find_dotenv
import secrets
import string
import hashlib
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"
    
    @classmethod
    def from_string(cls, value: str) -> 'Environment':
        """Convert string to Environment enum"""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.DEVELOPMENT


@dataclass
class ConfigValue:
    """Configuration value with metadata"""
    value: Any
    source: str  # env, file, default
    sensitive: bool = False
    description: str = ""
    validation: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "value": "***" if self.sensitive else self.value,
            "source": self.source,
            "sensitive": self.sensitive,
            "description": self.description
        }


class ConfigValidationError(Exception):
    """Configuration validation error"""
    pass


class ConfigNotFoundError(Exception):
    """Configuration not found error"""
    pass


@dataclass
class ConfigSchema:
    """Schema definition for configuration"""
    name: str
    type: Type
    required: bool = False
    default: Any = None
    description: str = ""
    sensitive: bool = False
    validator: Optional[Callable] = None
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    env_name: Optional[str] = None
    
    def validate(self, value: Any) -> Any:
        """Validate configuration value"""
        if value is None:
            if self.required:
                raise ConfigValidationError(f"Configuration '{self.name}' is required")
            return self.default
        
        # Type validation
        if self.type != Any:
            try:
                if self.type == bool:
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                elif self.type == int:
                    value = int(value)
                elif self.type == float:
                    value = float(value)
                elif self.type == list:
                    if isinstance(value, str):
                        value = [v.strip() for v in value.split(',')]
                elif self.type == dict:
                    if isinstance(value, str):
                        try:
                            value = json.loads(value)
                        except json.JSONDecodeError:
                            raise ConfigValidationError(f"Cannot parse '{self.name}' as JSON")
            except (ValueError, TypeError) as e:
                raise ConfigValidationError(f"Invalid type for '{self.name}': {e}")
        
        # Choices validation
        if self.choices and value not in self.choices:
            raise ConfigValidationError(
                f"Value '{value}' for '{self.name}' must be one of: {self.choices}"
            )
        
        # Range validation
        if self.min_value is not None and value < self.min_value:
            raise ConfigValidationError(
                f"Value '{value}' for '{self.name}' must be >= {self.min_value}"
            )
        if self.max_value is not None and value > self.max_value:
            raise ConfigValidationError(
                f"Value '{value}' for '{self.name}' must be <= {self.max_value}"
            )
        
        # Pattern validation
        if self.pattern and isinstance(value, str):
            if not re.match(self.pattern, value):
                raise ConfigValidationError(
                    f"Value '{value}' for '{self.name}' must match pattern: {self.pattern}"
                )
        
        # Custom validator
        if self.validator:
            try:
                value = self.validator(value)
            except Exception as e:
                raise ConfigValidationError(f"Validation failed for '{self.name}': {e}")
        
        return value


class SecretManager:
    """Manage secrets and sensitive configuration"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self._secrets: Dict[str, str] = {}
        self._encryption_key = encryption_key
    
    def set_secret(self, name: str, value: str, encrypt: bool = False):
        """Set a secret value"""
        if encrypt and self._encryption_key:
            value = self._encrypt(value)
        self._secrets[name] = value
    
    def get_secret(self, name: str, decrypt: bool = False) -> Optional[str]:
        """Get a secret value"""
        value = self._secrets.get(name)
        if value and decrypt and self._encryption_key:
            return self._decrypt(value)
        return value
    
    def _encrypt(self, value: str) -> str:
        """Simple encryption (use proper encryption in production)"""
        # This is a simple placeholder - use a proper encryption library in production
        if self._encryption_key:
            return hashlib.sha256(f"{self._encryption_key}{value}".encode()).hexdigest()[:32]
        return value
    
    def _decrypt(self, value: str) -> str:
        """Simple decryption"""
        # This is a placeholder - implement proper decryption in production
        return value
    
    def generate_secret(self, length: int = 32) -> str:
        """Generate a secure random secret"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class EnvironmentConfig:
    """Environment-based configuration manager"""
    
    def __init__(
        self,
        env_file: Optional[str] = None,
        prefix: str = "APP_",
        auto_load: bool = True,
        secret_manager: Optional[SecretManager] = None
    ):
        self._prefix = prefix
        self._secret_manager = secret_manager or SecretManager()
        self._config: Dict[str, ConfigValue] = {}
        self._schemas: Dict[str, ConfigSchema] = {}
        self._environment = Environment.LOCAL
        self._env_file = env_file
        self._loaded = False
        self._immutable = False
        self._overrides: Dict[str, Any] = {}
        
        if auto_load:
            self.load()
    
    def load(self, env_file: Optional[str] = None):
        """Load configuration from environment variables and files"""
        if self._loaded and self._immutable:
            raise RuntimeError("Configuration is immutable and already loaded")
        
        # Load .env file
        if env_file:
            load_dotenv(env_file)
        elif self._env_file:
            load_dotenv(self._env_file)
        else:
            # Try to find .env file automatically
            env_path = find_dotenv()
            if env_path:
                load_dotenv(env_path)
            else:
                # Try common locations
                for location in ['.env', '.env.local', '.env.development']:
                    if Path(location).exists():
                        load_dotenv(location)
                        break
        
        # Load environment-specific files
        env_name = self.get_environment().value
        env_file_paths = [
            f'.env.{env_name}',
            f'.env.{env_name}.local',
        ]
        for env_path in env_file_paths:
            if Path(env_path).exists():
                load_dotenv(env_path, override=True)
        
        # Detect environment
        self._detect_environment()
        
        # Load configuration
        self._load_from_env()
        self._loaded = True
    
    def _detect_environment(self):
        """Detect current environment"""
        env_str = os.getenv("ENVIRONMENT", "local")
        self._environment = Environment.from_string(env_str)
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_vars = self._get_env_vars()
        
        for key, value in env_vars.items():
            # Remove prefix
            config_key = key[len(self._prefix):] if key.startswith(self._prefix) else key
            
            # Check if this is a schema
            schema = self._schemas.get(config_key.lower())
            
            # Parse value
            parsed_value = self._parse_env_value(value, schema)
            
            # Store configuration
            self._config[config_key] = ConfigValue(
                value=parsed_value,
                source="env",
                sensitive=schema.sensitive if schema else False,
                description=schema.description if schema else ""
            )
    
    def _get_env_vars(self) -> Dict[str, str]:
        """Get all relevant environment variables"""
        env_vars = {}
        
        # Get all variables with prefix
        for key, value in os.environ.items():
            if key.startswith(self._prefix) or key in self._schemas:
                env_vars[key] = value
        
        return env_vars
    
    def _parse_env_value(self, value: str, schema: Optional[ConfigSchema] = None) -> Any:
        """Parse environment variable value based on type"""
        if not schema:
            return value
        
        if schema.type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif schema.type == int:
            return int(value)
        elif schema.type == float:
            return float(value)
        elif schema.type == list:
            return [v.strip() for v in value.split(',') if v.strip()]
        elif schema.type == dict:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Try YAML
                try:
                    return yaml.safe_load(value)
                except yaml.YAMLError:
                    return value
        else:
            return value
    
    def register_schema(self, schema: ConfigSchema):
        """Register a configuration schema"""
        key = schema.env_name or schema.name
        self._schemas[key.lower()] = schema
        
        # If value already loaded, re-parse with schema
        if key in self._config:
            config_value = self._config[key]
            try:
                validated_value = schema.validate(config_value.value)
                self._config[key] = ConfigValue(
                    value=validated_value,
                    source=config_value.source,
                    sensitive=schema.sensitive,
                    description=schema.description
                )
            except ConfigValidationError as e:
                logger.warning(f"Invalid configuration value for '{key}': {e}")
    
    def register_schemas(self, schemas: List[ConfigSchema]):
        """Register multiple schemas"""
        for schema in schemas:
            self.register_schema(schema)
    
    def get(self, key: str, default: Any = None, validate: bool = True) -> Any:
        """Get configuration value"""
        key_lower = key.lower()
        
        # Check overrides first
        if key_lower in self._overrides:
            return self._overrides[key_lower]
        
        # Check configuration
        if key_lower in self._config:
            return self._config[key_lower].value
        
        # Check schema
        if key_lower in self._schemas:
            schema = self._schemas[key_lower]
            if schema.default is not None:
                return schema.default
        
        # Check environment variable
        env_key = f"{self._prefix}{key}".upper()
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._parse_env_value(env_value, self._schemas.get(key_lower))
        
        # Return default
        return default
    
    def get_typed(self, key: str, type_hint: Type) -> Any:
        """Get configuration value with type hint"""
        value = self.get(key)
        if value is None:
            return None
        
        try:
            if type_hint == bool:
                if isinstance(value, str):
                    return value.lower() in ('true', '1', 'yes', 'on')
                return bool(value)
            elif type_hint == int:
                return int(value)
            elif type_hint == float:
                return float(value)
            elif type_hint == list:
                if isinstance(value, str):
                    return [v.strip() for v in value.split(',')]
                return list(value)
            elif type_hint == dict:
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return yaml.safe_load(value)
                return dict(value)
            else:
                return value
        except (ValueError, TypeError) as e:
            raise ConfigValidationError(f"Cannot convert '{key}' to {type_hint}: {e}")
    
    def get_secret(self, key: str, decrypt: bool = False) -> Optional[str]:
        """Get secret value"""
        key_lower = key.lower()
        
        # Check secret manager first
        secret = self._secret_manager.get_secret(key_lower, decrypt)
        if secret is not None:
            return secret
        
        # Then check environment
        value = self.get(key)
        if value and self._config.get(key_lower, ConfigValue(value=value, source="env")).sensitive:
            return str(value)
        
        return None
    
    def set(self, key: str, value: Any, source: str = "manual", sensitive: bool = False):
        """Set configuration value"""
        if self._immutable:
            raise RuntimeError("Configuration is immutable")
        
        key_lower = key.lower()
        
        # Validate against schema
        if key_lower in self._schemas:
            value = self._schemas[key_lower].validate(value)
            sensitive = sensitive or self._schemas[key_lower].sensitive
        
        self._config[key_lower] = ConfigValue(
            value=value,
            source=source,
            sensitive=sensitive
        )
    
    def override(self, key: str, value: Any):
        """Override configuration value (temporary)"""
        self._overrides[key.lower()] = value
    
    def clear_overrides(self):
        """Clear all overrides"""
        self._overrides.clear()
    
    def get_all(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Get all configuration values"""
        result = {}
        for key, config_value in self._config.items():
            if not include_sensitive and config_value.sensitive:
                result[key] = "***"
            else:
                result[key] = config_value.value
        
        # Add schema defaults not yet set
        for key, schema in self._schemas.items():
            if key not in result and schema.default is not None:
                result[key] = schema.default
        
        return result
    
    def get_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration metadata"""
        result = {}
        for key, config_value in self._config.items():
            result[key] = config_value.to_dict()
        
        # Add schema information
        for key, schema in self._schemas.items():
            if key not in result:
                result[key] = {
                    "value": schema.default,
                    "source": "schema",
                    "sensitive": schema.sensitive,
                    "description": schema.description
                }
        
        return result
    
    def validate_all(self) -> bool:
        """Validate all configuration values"""
        valid = True
        for key, schema in self._schemas.items():
            try:
                value = self.get(key)
                schema.validate(value)
            except ConfigValidationError as e:
                logger.error(f"Configuration validation failed for '{key}': {e}")
                valid = False
        
        return valid
    
    def get_environment(self) -> Environment:
        """Get current environment"""
        return self._environment
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self._environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self._environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self._environment == Environment.TESTING
    
    def require(self, key: str) -> Any:
        """Get required configuration value (raises if not set)"""
        value = self.get(key)
        if value is None:
            raise ConfigNotFoundError(f"Required configuration '{key}' not found")
        return value
    
    def reload(self):
        """Reload configuration from environment"""
        self._config.clear()
        self._loaded = False
        self.load()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.get_all(include_sensitive=True)
    
    def to_env_file(self, path: str, include_sensitive: bool = False):
        """Generate .env file from configuration"""
        content = []
        for key, value in self.get_all(include_sensitive=include_sensitive).items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            content.append(f"{self._prefix}{key.upper()}={value}")
        
        with open(path, 'w') as f:
            f.write('\n'.join(content))
    
    def add_schema_from_class(self, cls: Type, prefix: str = ""):
        """Add schema from dataclass"""
        if hasattr(cls, '__annotations__'):
            for field_name, field_type in cls.__annotations__.items():
                schema = ConfigSchema(
                    name=f"{prefix}{field_name}" if prefix else field_name,
                    type=field_type,
                    default=getattr(cls, field_name, None)
                )
                self.register_schema(schema)


class ConfigBuilder:
    """Builder for creating configuration with schemas"""
    
    def __init__(self):
        self.schemas: List[ConfigSchema] = []
        self.prefix: str = "APP_"
        self.env_file: Optional[str] = None
    
    def add(self, schema: ConfigSchema) -> 'ConfigBuilder':
        """Add a schema"""
        self.schemas.append(schema)
        return self
    
    def add_from_class(self, cls: Type, prefix: str = "") -> 'ConfigBuilder':
        """Add schemas from a class"""
        if hasattr(cls, '__annotations__'):
            for field_name, field_type in cls.__annotations__.items():
                schema = ConfigSchema(
                    name=f"{prefix}{field_name}" if prefix else field_name,
                    type=field_type,
                    default=getattr(cls, field_name, None)
                )
                self.schemas.append(schema)
        return self
    
    def set_prefix(self, prefix: str) -> 'ConfigBuilder':
        """Set environment variable prefix"""
        self.prefix = prefix
        return self
    
    def set_env_file(self, env_file: str) -> 'ConfigBuilder':
        """Set environment file"""
        self.env_file = env_file
        return self
    
    def build(self) -> EnvironmentConfig:
        """Build the configuration"""
        config = EnvironmentConfig(env_file=self.env_file, prefix=self.prefix)
        for schema in self.schemas:
            config.register_schema(schema)
        return config


# Common configuration schemas
class CommonConfigSchemas:
    """Common configuration schemas"""
    
    @staticmethod
    def database_config(prefix: str = "DB_") -> List[ConfigSchema]:
        """Database configuration schemas"""
        return [
            ConfigSchema(
                name="host",
                type=str,
                required=True,
                description="Database host",
                env_name=f"{prefix}HOST"
            ),
            ConfigSchema(
                name="port",
                type=int,
                default=5432,
                description="Database port",
                min_value=1,
                max_value=65535,
                env_name=f"{prefix}PORT"
            ),
            ConfigSchema(
                name="name",
                type=str,
                required=True,
                description="Database name",
                env_name=f"{prefix}NAME"
            ),
            ConfigSchema(
                name="user",
                type=str,
                required=True,
                description="Database user",
                env_name=f"{prefix}USER"
            ),
            ConfigSchema(
                name="password",
                type=str,
                required=True,
                sensitive=True,
                description="Database password",
                env_name=f"{prefix}PASSWORD"
            ),
            ConfigSchema(
                name="pool_size",
                type=int,
                default=10,
                description="Connection pool size",
                min_value=1,
                max_value=100,
                env_name=f"{prefix}POOL_SIZE"
            )
        ]
    
    @staticmethod
    def redis_config(prefix: str = "REDIS_") -> List[ConfigSchema]:
        """Redis configuration schemas"""
        return [
            ConfigSchema(
                name="host",
                type=str,
                default="localhost",
                description="Redis host",
                env_name=f"{prefix}HOST"
            ),
            ConfigSchema(
                name="port",
                type=int,
                default=6379,
                description="Redis port",
                min_value=1,
                max_value=65535,
                env_name=f"{prefix}PORT"
            ),
            ConfigSchema(
                name="password",
                type=str,
                sensitive=True,
                description="Redis password",
                env_name=f"{prefix}PASSWORD"
            ),
            ConfigSchema(
                name="db",
                type=int,
                default=0,
                description="Redis database number",
                min_value=0,
                max_value=15,
                env_name=f"{prefix}DB"
            )
        ]
    
    @staticmethod
    def api_config(prefix: str = "API_") -> List[ConfigSchema]:
        """API configuration schemas"""
        return [
            ConfigSchema(
                name="host",
                type=str,
                default="0.0.0.0",
                description="API host",
                env_name=f"{prefix}HOST"
            ),
            ConfigSchema(
                name="port",
                type=int,
                default=8000,
                description="API port",
                min_value=1,
                max_value=65535,
                env_name=f"{prefix}PORT"
            ),
            ConfigSchema(
                name="debug",
                type=bool,
                default=False,
                description="Debug mode",
                env_name=f"{prefix}DEBUG"
            ),
            ConfigSchema(
                name="secret_key",
                type=str,
                required=True,
                sensitive=True,
                description="API secret key",
                min_length=32,
                env_name=f"{prefix}SECRET_KEY"
            ),
            ConfigSchema(
                name="cors_origins",
                type=list,
                default=["*"],
                description="CORS allowed origins",
                env_name=f"{prefix}CORS_ORIGINS"
            )
        ]
    
    @staticmethod
    def logging_config(prefix: str = "LOG_") -> List[ConfigSchema]:
        """Logging configuration schemas"""
        return [
            ConfigSchema(
                name="level",
                type=str,
                default="INFO",
                description="Log level",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                env_name=f"{prefix}LEVEL"
            ),
            ConfigSchema(
                name="format",
                type=str,
                default="json",
                description="Log format",
                choices=["json", "text"],
                env_name=f"{prefix}FORMAT"
            ),
            ConfigSchema(
                name="file",
                type=str,
                description="Log file path",
                env_name=f"{prefix}FILE"
            )
        ]


# Singleton instance
_config_instance: Optional[EnvironmentConfig] = None


def get_config() -> EnvironmentConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance


def init_config(
    env_file: Optional[str] = None,
    prefix: str = "APP_",
    schemas: Optional[List[ConfigSchema]] = None
) -> EnvironmentConfig:
    """Initialize global configuration"""
    global _config_instance
    _config_instance = EnvironmentConfig(env_file=env_file, prefix=prefix)
    if schemas:
        for schema in schemas:
            _config_instance.register_schema(schema)
    return _config_instance


# Example configuration dataclass
@dataclass
class AppConfig:
    """Application configuration"""
    environment: str = "local"
    debug: bool = False
    secret_key: str = ""
    database_url: str = ""
    redis_url: str = ""
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    @classmethod
    def from_env(cls, env_config: Optional[EnvironmentConfig] = None) -> 'AppConfig':
        """Create from environment configuration"""
        config = env_config or get_config()
        return cls(
            environment=config.get_environment().value,
            debug=config.get("debug", False),
            secret_key=config.get_secret("secret_key", True) or "",
            database_url=config.get("database_url", ""),
            redis_url=config.get("redis_url", ""),
            api_host=config.get("api_host", "0.0.0.0"),
            api_port=config.get("api_port", 8000),
            log_level=config.get("log_level", "INFO"),
            cors_origins=config.get("cors_origins", ["*"])
        )


# Example usage and tests
def test_environment_config():
    """Test environment configuration"""
    
    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION TESTS")
    print("=" * 60)
    
    # Setup test environment
    os.environ["ENVIRONMENT"] = "development"
    os.environ["APP_DEBUG"] = "true"
    os.environ["APP_SECRET_KEY"] = "test-secret-key-12345"
    os.environ["APP_DATABASE_URL"] = "postgresql://localhost:5432/testdb"
    os.environ["APP_CORS_ORIGINS"] = "http://localhost:3000,https://example.com"
    os.environ["APP_LOG_LEVEL"] = "DEBUG"
    
    # Create configuration with schemas
    print("\n1. Creating configuration with schemas")
    print("-" * 40)
    
    schemas = [
        ConfigSchema(
            name="debug",
            type=bool,
            default=False,
            description="Debug mode",
            env_name="APP_DEBUG"
        ),
        ConfigSchema(
            name="secret_key",
            type=str,
            required=True,
            sensitive=True,
            description="Secret key",
            min_length=10,
            env_name="APP_SECRET_KEY"
        ),
        ConfigSchema(
            name="database_url",
            type=str,
            description="Database URL",
            env_name="APP_DATABASE_URL"
        ),
        ConfigSchema(
            name="cors_origins",
            type=list,
            default=[],
            description="CORS origins",
            env_name="APP_CORS_ORIGINS"
        ),
        ConfigSchema(
            name="log_level",
            type=str,
            default="INFO",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            env_name="APP_LOG_LEVEL"
        )
    ]
    
    config = EnvironmentConfig(prefix="APP_")
    for schema in schemas:
        config.register_schema(schema)
    config.load()
    
    # Test getting values
    print("\n2. Getting configuration values")
    print("-" * 40)
    print(f"Environment: {config.get_environment().value}")
    print(f"Debug: {config.get('debug')}")
    print(f"Secret Key: {config.get_secret('secret_key')}")
    print(f"Database URL: {config.get('database_url')}")
    print(f"CORS Origins: {config.get('cors_origins')}")
    print(f"Log Level: {config.get('log_level')}")
    
    # Test validation
    print("\n3. Validating configuration")
    print("-" * 40)
    valid = config.validate_all()
    print(f"Configuration valid: {valid}")
    
    # Test metadata
    print("\n4. Configuration metadata")
    print("-" * 40)
    metadata = config.get_metadata()
    for key, info in list(metadata.items())[:3]:
        print(f"{key}: {info}")
    
    # Test setting values
    print("\n5. Setting and overriding values")
    print("-" * 40)
    config.set("custom_value", "test", source="manual")
    print(f"Custom value: {config.get('custom_value')}")
    
    config.override("debug", False)
    print(f"Overridden debug: {config.get('debug')}")
    
    config.clear_overrides()
    print(f"Cleared debug: {config.get('debug')}")
    
    # Test using builder
    print("\n6. Using ConfigBuilder")
    print("-" * 40)
    builder = (ConfigBuilder()
               .set_prefix("TEST_")
               .add(ConfigSchema("test_key", str, default="test"))
               .add(ConfigSchema("test_int", int, default=42)))
    
    test_config = builder.build()
    print(f"Test key: {test_config.get('test_key')}")
    print(f"Test int: {test_config.get('test_int')}")
    
    # Test from dataclass
    print("\n7. Using dataclass integration")
    print("-" * 40)
    app_config = AppConfig.from_env(config)
    print(f"App config: {app_config}")
    
    # Test secret generation
    print("\n8. Secret generation")
    print("-" * 40)
    secret_manager = SecretManager()
    new_secret = secret_manager.generate_secret(32)
    print(f"Generated secret: {new_secret}")
    
    # Test environment detection
    print("\n9. Environment detection")
    print("-" * 40)
    for env in Environment:
        os.environ["ENVIRONMENT"] = env.value
        config.reload()
        print(f"{env.value}: {config.get_environment().value}")
    
    # Test to_env_file
    print("\n10. Export to .env file")
    print("-" * 40)
    config.to_env_file("test_env_export.env")
    print("Created test_env_export.env")
    with open("test_env_export.env", "r") as f:
        content = f.read()
        print(f"Content:\n{content[:200]}...")
    
    # Cleanup
    os.remove("test_env_export.env")
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_environment_config()
