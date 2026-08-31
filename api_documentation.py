"""
api_documentation.py
A comprehensive API documentation module with automatic generation and interactive features
"""

import inspect
import json
from typing import Optional, Dict, Any, List, Union, Callable, Type, get_type_hints
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
import re
from functools import wraps
import yaml
from pathlib import Path


class HttpMethod(Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class Parameter:
    """API parameter definition"""
    name: str
    type: str
    required: bool = False
    description: str = ""
    default: Any = None
    example: Any = None
    enum_values: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.example is not None:
            result["example"] = self.example
        if self.enum_values:
            result["enum"] = self.enum_values
        if self.min_value is not None:
            result["min"] = self.min_value
        if self.max_value is not None:
            result["max"] = self.max_value
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        if self.pattern:
            result["pattern"] = self.pattern
        return result


@dataclass
class Response:
    """API response definition"""
    status_code: int
    description: str
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "status_code": self.status_code,
            "description": self.description,
        }
        if self.schema:
            result["schema"] = self.schema
        if self.example is not None:
            result["example"] = self.example
        return result


@dataclass
class Endpoint:
    """API endpoint definition"""
    path: str
    method: HttpMethod
    summary: str = ""
    description: str = ""
    parameters: List[Parameter] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: List[Response] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    authentication_required: bool = True
    rate_limit: Optional[str] = None
    examples: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "method": self.method.value,
            "summary": self.summary,
            "description": self.description,
            "parameters": [p.to_dict() for p in self.parameters],
            "request_body": self.request_body,
            "responses": [r.to_dict() for r in self.responses],
            "tags": self.tags,
            "deprecated": self.deprecated,
            "authentication_required": self.authentication_required,
            "rate_limit": self.rate_limit,
            "examples": self.examples,
            "errors": self.errors,
            "notes": self.notes,
        }


@dataclass
class APIDocumentation:
    """Complete API documentation"""
    title: str
    version: str
    description: str = ""
    base_url: str = ""
    endpoints: List[Endpoint] = field(default_factory=list)
    schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    authentication: Dict[str, Any] = field(default_factory=dict)
    rate_limits: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    changelog: List[Dict[str, Any]] = field(default_factory=list)
    contact: Dict[str, str] = field(default_factory=dict)
    license: Dict[str, str] = field(default_factory=dict)
    external_docs: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "version": self.version,
            "description": self.description,
            "base_url": self.base_url,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "schemas": self.schemas,
            "authentication": self.authentication,
            "rate_limits": self.rate_limits,
            "tags": self.tags,
            "changelog": self.changelog,
            "contact": self.contact,
            "license": self.license,
            "external_docs": self.external_docs,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def to_yaml(self) -> str:
        """Convert to YAML"""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)
    
    def to_markdown(self) -> str:
        """Convert to Markdown"""
        return DocumentationFormatter.to_markdown(self)
    
    def to_openapi(self) -> Dict[str, Any]:
        """Convert to OpenAPI 3.0 specification"""
        return OpenAPIGenerator.generate(self)


class DocumentationFormatter:
    """Format API documentation in different formats"""
    
    @staticmethod
    def to_markdown(doc: APIDocumentation) -> str:
        """Generate Markdown documentation"""
        lines = []
        
        # Header
        lines.append(f"# {doc.title} API Documentation")
        lines.append(f"Version: {doc.version}")
        lines.append("")
        if doc.description:
            lines.append(doc.description)
            lines.append("")
        
        # Base URL
        if doc.base_url:
            lines.append(f"**Base URL:** `{doc.base_url}`")
            lines.append("")
        
        # Authentication
        if doc.authentication:
            lines.append("## Authentication")
            lines.append("")
            for key, value in doc.authentication.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        
        # Rate Limits
        if doc.rate_limits:
            lines.append("## Rate Limits")
            lines.append("")
            for key, value in doc.rate_limits.items():
                lines.append(f"- **{key}:** {value}")
            lines.append("")
        
        # Tags
        if doc.tags:
            lines.append("## Tags")
            lines.append("")
            for tag, description in doc.tags.items():
                lines.append(f"- **{tag}:** {description}")
            lines.append("")
        
        # Endpoints
        lines.append("## Endpoints")
        lines.append("")
        
        for endpoint in doc.endpoints:
            lines.extend(DocumentationFormatter._endpoint_to_markdown(endpoint))
        
        # Schemas
        if doc.schemas:
            lines.append("## Schemas")
            lines.append("")
            for name, schema in doc.schemas.items():
                lines.append(f"### {name}")
                lines.append("```json")
                lines.append(json.dumps(schema, indent=2))
                lines.append("```")
                lines.append("")
        
        # Changelog
        if doc.changelog:
            lines.append("## Changelog")
            lines.append("")
            for entry in doc.changelog:
                version = entry.get("version", "Unknown")
                date = entry.get("date", "")
                changes = entry.get("changes", [])
                lines.append(f"### {version} ({date})")
                for change in changes:
                    lines.append(f"- {change}")
                lines.append("")
        
        # Contact
        if doc.contact:
            lines.append("## Contact")
            lines.append("")
            for key, value in doc.contact.items():
                lines.append(f"- **{key.capitalize()}:** {value}")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def _endpoint_to_markdown(endpoint: Endpoint) -> List[str]:
        """Convert a single endpoint to Markdown"""
        lines = []
        
        # Endpoint header
        method_color = {
            HttpMethod.GET: "🟢",
            HttpMethod.POST: "🟡",
            HttpMethod.PUT: "🔵",
            HttpMethod.DELETE: "🔴",
            HttpMethod.PATCH: "🟣",
        }.get(endpoint.method, "⚪")
        
        title = f"### {method_color} `{endpoint.method.value}` {endpoint.path}"
        if endpoint.deprecated:
            title += " ⚠️ **DEPRECATED**"
        lines.append(title)
        lines.append("")
        
        # Summary and description
        if endpoint.summary:
            lines.append(f"**Summary:** {endpoint.summary}")
            lines.append("")
        if endpoint.description:
            lines.append(endpoint.description)
            lines.append("")
        
        # Authentication
        lines.append(f"**Authentication:** {'Required' if endpoint.authentication_required else 'Not required'}")
        if endpoint.rate_limit:
            lines.append(f"**Rate Limit:** {endpoint.rate_limit}")
        lines.append("")
        
        # Parameters
        if endpoint.parameters:
            lines.append("#### Parameters")
            lines.append("")
            lines.append("| Name | Type | Required | Description |")
            lines.append("|------|------|----------|-------------|")
            for param in endpoint.parameters:
                required = "✅" if param.required else "❌"
                type_info = param.type
                if param.enum_values:
                    type_info += f" (enum: {', '.join(str(v) for v in param.enum_values)})"
                if param.default is not None:
                    type_info += f" (default: {param.default})"
                if param.example is not None:
                    type_info += f" (example: {param.example})"
                lines.append(f"| {param.name} | {type_info} | {required} | {param.description} |")
            lines.append("")
        
        # Request body
        if endpoint.request_body:
            lines.append("#### Request Body")
            lines.append("")
            lines.append("```json")
            lines.append(json.dumps(endpoint.request_body, indent=2))
            lines.append("```")
            lines.append("")
        
        # Responses
        if endpoint.responses:
            lines.append("#### Responses")
            lines.append("")
            for response in endpoint.responses:
                emoji = "✅" if 200 <= response.status_code < 300 else "❌"
                lines.append(f"**{emoji} {response.status_code}** {response.description}")
                if response.schema:
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(response.schema, indent=2))
                    lines.append("```")
                if response.example is not None:
                    lines.append("")
                    lines.append("**Example:**")
                    lines.append("```json")
                    lines.append(json.dumps(response.example, indent=2))
                    lines.append("```")
                lines.append("")
        
        # Examples
        if endpoint.examples:
            lines.append("#### Examples")
            lines.append("")
            for i, example in enumerate(endpoint.examples, 1):
                lines.append(f"**Example {i}:** {example.get('description', '')}")
                if "request" in example:
                    lines.append("Request:")
                    lines.append("```bash")
                    lines.append(example["request"])
                    lines.append("```")
                if "response" in example:
                    lines.append("Response:")
                    lines.append("```json")
                    lines.append(json.dumps(example["response"], indent=2))
                    lines.append("```")
                lines.append("")
        
        # Errors
        if endpoint.errors:
            lines.append("#### Error Codes")
            lines.append("")
            lines.append("| Code | Message | Description |")
            lines.append("|------|---------|-------------|")
            for error in endpoint.errors:
                lines.append(f"| {error.get('code', '')} | {error.get('message', '')} | {error.get('description', '')} |")
            lines.append("")
        
        # Notes
        if endpoint.notes:
            lines.append("#### Notes")
            lines.append("")
            for note in endpoint.notes:
                lines.append(f"- {note}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        return lines


class OpenAPIGenerator:
    """Generate OpenAPI 3.0 specification"""
    
    @staticmethod
    def generate(doc: APIDocumentation) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 spec"""
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": doc.title,
                "version": doc.version,
                "description": doc.description,
            },
            "paths": {},
            "components": {
                "schemas": doc.schemas,
                "securitySchemes": {}
            },
            "tags": [],
            "security": []
        }
        
        # Add contact
        if doc.contact:
            openapi["info"]["contact"] = doc.contact
        
        # Add license
        if doc.license:
            openapi["info"]["license"] = doc.license
        
        # Add external docs
        if doc.external_docs:
            openapi["externalDocs"] = {"url": doc.external_docs}
        
        # Add tags
        for tag, description in doc.tags.items():
            openapi["tags"].append({"name": tag, "description": description})
        
        # Add authentication
        if doc.authentication:
            if "type" in doc.authentication:
                auth_type = doc.authentication["type"].lower()
                if auth_type == "api_key":
                    openapi["components"]["securitySchemes"]["ApiKeyAuth"] = {
                        "type": "apiKey",
                        "in": doc.authentication.get("in", "header"),
                        "name": doc.authentication.get("name", "X-API-Key")
                    }
                    openapi["security"].append({"ApiKeyAuth": []})
                elif auth_type == "bearer":
                    openapi["components"]["securitySchemes"]["BearerAuth"] = {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": doc.authentication.get("format", "JWT")
                    }
                    openapi["security"].append({"BearerAuth": []})
                elif auth_type == "oauth2":
                    openapi["components"]["securitySchemes"]["OAuth2"] = {
                        "type": "oauth2",
                        "flows": doc.authentication.get("flows", {})
                    }
                    openapi["security"].append({"OAuth2": []})
        
        # Add endpoints
        for endpoint in doc.endpoints:
            path_item = openapi["paths"].setdefault(endpoint.path, {})
            operation = OpenAPIGenerator._endpoint_to_operation(endpoint)
            path_item[endpoint.method.value.lower()] = operation
        
        return openapi
    
    @staticmethod
    def _endpoint_to_operation(endpoint: Endpoint) -> Dict[str, Any]:
        """Convert endpoint to OpenAPI operation"""
        operation = {
            "summary": endpoint.summary,
            "description": endpoint.description,
            "tags": endpoint.tags if endpoint.tags else ["default"],
            "parameters": [],
            "responses": {},
            "deprecated": endpoint.deprecated
        }
        
        # Add parameters
        for param in endpoint.parameters:
            param_dict = {
                "name": param.name,
                "in": "query",  # Default to query, could be path or header
                "required": param.required,
                "description": param.description,
                "schema": {
                    "type": OpenAPIGenerator._type_mapping(param.type)
                }
            }
            
            if param.enum_values:
                param_dict["schema"]["enum"] = param.enum_values
            if param.example is not None:
                param_dict["schema"]["example"] = param.example
            if param.min_value is not None:
                param_dict["schema"]["minimum"] = param.min_value
            if param.max_value is not None:
                param_dict["schema"]["maximum"] = param.max_value
            
            operation["parameters"].append(param_dict)
        
        # Add request body
        if endpoint.request_body:
            operation["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": endpoint.request_body
                    }
                },
                "required": True
            }
        
        # Add responses
        for response in endpoint.responses:
            response_dict = {
                "description": response.description
            }
            if response.schema:
                response_dict["content"] = {
                    "application/json": {
                        "schema": response.schema
                    }
                }
            if response.example is not None:
                if "content" not in response_dict:
                    response_dict["content"] = {
                        "application/json": {}
                    }
                response_dict["content"]["application/json"]["example"] = response.example
            
            operation["responses"][str(response.status_code)] = response_dict
        
        return operation
    
    @staticmethod
    def _type_mapping(python_type: str) -> str:
        """Map Python type to OpenAPI type"""
        mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "NoneType": "null"
        }
        return mapping.get(python_type.lower(), "string")


class APIDocGenerator:
    """Generate API documentation from code"""
    
    def __init__(self, title: str, version: str, description: str = ""):
        self.doc = APIDocumentation(
            title=title,
            version=version,
            description=description
        )
        self._current_tags = []
    
    def add_endpoint(
        self,
        path: str,
        method: HttpMethod,
        summary: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
        **kwargs
    ) -> 'APIDocGenerator':
        """Add an endpoint to documentation"""
        endpoint = Endpoint(
            path=path,
            method=method,
            summary=summary,
            description=description,
            tags=tags or self._current_tags.copy(),
            **kwargs
        )
        self.doc.endpoints.append(endpoint)
        return self
    
    def tag(self, name: str, description: str = "") -> 'APIDocGenerator':
        """Add a tag and set it as current"""
        self.doc.tags[name] = description
        self._current_tags.append(name)
        return self
    
    def schema(self, name: str, schema: Dict[str, Any]) -> 'APIDocGenerator':
        """Add a schema"""
        self.doc.schemas[name] = schema
        return self
    
    def authentication(self, **kwargs) -> 'APIDocGenerator':
        """Set authentication configuration"""
        self.doc.authentication = kwargs
        return self
    
    def rate_limit(self, **kwargs) -> 'APIDocGenerator':
        """Set rate limits"""
        self.doc.rate_limits = kwargs
        return self
    
    def changelog_entry(self, version: str, date: str, changes: List[str]) -> 'APIDocGenerator':
        """Add changelog entry"""
        self.doc.changelog.append({
            "version": version,
            "date": date,
            "changes": changes
        })
        return self
    
    def contact(self, **kwargs) -> 'APIDocGenerator':
        """Set contact information"""
        self.doc.contact = kwargs
        return self
    
    def license(self, **kwargs) -> 'APIDocGenerator':
        """Set license information"""
        self.doc.license = kwargs
        return self
    
    def build(self) -> APIDocumentation:
        """Build the documentation"""
        return self.doc
    
    def save(self, filename: str, format: str = "json"):
        """Save documentation to file"""
        doc = self.build()
        
        if format == "json":
            with open(filename, 'w') as f:
                f.write(doc.to_json())
        elif format == "yaml":
            with open(filename, 'w') as f:
                f.write(doc.to_yaml())
        elif format == "md":
            with open(filename, 'w') as f:
                f.write(doc.to_markdown())
        elif format == "openapi":
            with open(filename, 'w') as f:
                json.dump(doc.to_openapi(), f, indent=2)


def document_endpoint(
    path: str,
    method: HttpMethod,
    summary: str = "",
    description: str = "",
    tags: Optional[List[str]] = None,
    parameters: Optional[List[Parameter]] = None,
    responses: Optional[List[Response]] = None,
    authentication_required: bool = True,
    rate_limit: Optional[str] = None,
    examples: Optional[List[Dict[str, Any]]] = None,
    errors: Optional[List[Dict[str, str]]] = None,
    notes: Optional[List[str]] = None
):
    """Decorator to document an API endpoint function"""
    def decorator(func):
        # Store documentation on the function
        func._api_doc = {
            "path": path,
            "method": method,
            "summary": summary,
            "description": description,
            "tags": tags or [],
            "parameters": parameters or [],
            "responses": responses or [],
            "authentication_required": authentication_required,
            "rate_limit": rate_limit,
            "examples": examples or [],
            "errors": errors or [],
            "notes": notes or [],
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


class InteractiveAPIDoc:
    """Interactive API documentation with examples"""
    
    def __init__(self, doc: APIDocumentation, client=None):
        self.doc = doc
        self.client = client
    
    def display(self):
        """Display interactive documentation"""
        print(f"\n{'='*60}")
        print(f"{self.doc.title} - Interactive Documentation")
        print(f"{'='*60}\n")
        
        print(f"Version: {self.doc.version}")
        if self.doc.description:
            print(f"\n{self.doc.description}")
        
        print(f"\nBase URL: {self.doc.base_url}")
        
        # Display endpoints
        print("\nAvailable Endpoints:")
        print("-" * 60)
        for i, endpoint in enumerate(self.doc.endpoints, 1):
            status = "⚠️ DEPRECATED" if endpoint.deprecated else "✅"
            print(f"{i}. {status} {endpoint.method.value} {endpoint.path}")
            print(f"   {endpoint.summary}")
            print()
    
    def get_endpoint_help(self, endpoint_index: int) -> str:
        """Get help for a specific endpoint"""
        if 0 <= endpoint_index < len(self.doc.endpoints):
            endpoint = self.doc.endpoints[endpoint_index]
            return DocumentationFormatter._endpoint_to_markdown(endpoint)
        return "Endpoint not found"
    
    def execute_example(self, endpoint_index: int, example_index: int = 0):
        """Execute an example for an endpoint"""
        if 0 <= endpoint_index < len(self.doc.endpoints):
            endpoint = self.doc.endpoints[endpoint_index]
            if endpoint.examples and example_index < len(endpoint.examples):
                example = endpoint.examples[example_index]
                if self.client and "request" in example:
                    # Execute the example request
                    # This would need to be implemented based on the client
                    print(f"Executing example: {example.get('description', '')}")
                    return example.get("response", {})
        return None


# Example usage
def create_sample_documentation() -> APIDocumentation:
    """Create sample API documentation"""
    
    builder = APIDocGenerator(
        title="User Management API",
        version="1.0.0",
        description="A comprehensive API for managing users"
    )
    
    # Add tags
    builder.tag("Users", "User management operations")
    builder.tag("Admin", "Administrative operations")
    builder.tag("Authentication", "Authentication and authorization")
    
    # Add schemas
    builder.schema("User", {
        "type": "object",
        "properties": {
            "id": {"type": "integer", "example": 1},
            "name": {"type": "string", "example": "John Doe"},
            "email": {"type": "string", "format": "email", "example": "john@example.com"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150, "example": 30},
            "status": {"type": "string", "enum": ["active", "inactive", "pending"]}
        }
    })
    
    builder.schema("ErrorResponse", {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "message": {"type": "string"},
            "details": {"type": "object"}
        }
    })
    
    # Add authentication
    builder.authentication(
        type="Bearer",
        format="JWT",
        description="Use Bearer token for authentication"
    )
    
    # Add rate limits
    builder.rate_limit(
        default="1000 requests per hour",
        authenticated="10000 requests per hour"
    )
    
    # Add contact
    builder.contact(
        name="API Support",
        email="support@example.com",
        url="https://api.example.com/support"
    )
    
    # Add license
    builder.license(
        name="MIT License",
        url="https://opensource.org/licenses/MIT"
    )
    
    # Add changelog
    builder.changelog_entry("1.0.0", "2024-01-15", [
        "Initial API release",
        "Added user CRUD operations",
        "Added authentication"
    ])
    
    # Add endpoints
    
    # GET /users - List users
    builder.add_endpoint(
        path="/users",
        method=HttpMethod.GET,
        summary="List all users",
        description="Retrieve a paginated list of all users",
        tags=["Users"],
        parameters=[
            Parameter("page", "integer", False, "Page number", 1, 1),
            Parameter("size", "integer", False, "Items per page", 20, 20, min_value=1, max_value=100),
            Parameter("status", "string", False, "Filter by status", enum_values=["active", "inactive", "pending"]),
            Parameter("search", "string", False, "Search in name and email")
        ],
        responses=[
            Response(200, "Success", 
                schema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "array", "items": {"$ref": "#/components/schemas/User"}},
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "page": {"type": "integer"},
                                "size": {"type": "integer"},
                                "total": {"type": "integer"},
                                "total_pages": {"type": "integer"}
                            }
                        }
                    }
                },
                example={
                    "data": [
                        {"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30, "status": "active"},
                        {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "age": 25, "status": "active"}
                    ],
                    "pagination": {"page": 1, "size": 20, "total": 2, "total_pages": 1}
                }
            ),
            Response(400, "Bad request"),
            Response(401, "Unauthorized"),
            Response(429, "Rate limit exceeded")
        ],
        examples=[
            {
                "description": "List active users",
                "request": "GET /users?status=active&page=1&size=20",
                "response": {
                    "data": [{"id": 1, "name": "John Doe", "status": "active"}],
                    "pagination": {"page": 1, "size": 20, "total": 1, "total_pages": 1}
                }
            }
        ],
        errors=[
            {"code": "INVALID_PAGE", "message": "Invalid page number", "description": "Page must be greater than 0"},
            {"code": "INVALID_SIZE", "message": "Invalid size", "description": "Size must be between 1 and 100"}
        ],
        notes=[
            "Results are sorted by creation date descending",
            "Search is case-insensitive"
        ],
        authentication_required=False,
        rate_limit="1000 requests per hour"
    )
    
    # POST /users - Create user
    builder.add_endpoint(
        path="/users",
        method=HttpMethod.POST,
        summary="Create a new user",
        description="Create a new user with the provided information",
        tags=["Users"],
        request_body={
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {"type": "string", "example": "John Doe"},
                "email": {"type": "string", "format": "email", "example": "john@example.com"},
                "age": {"type": "integer", "minimum": 0, "maximum": 150, "example": 30},
                "status": {"type": "string", "enum": ["active", "inactive", "pending"], "example": "active"}
            }
        },
        responses=[
            Response(201, "User created", 
                schema={"$ref": "#/components/schemas/User"},
                example={"id": 3, "name": "John Doe", "email": "john@example.com", "age": 30, "status": "active"}
            ),
            Response(400, "Invalid input"),
            Response(409, "User already exists")
        ],
        examples=[
            {
                "description": "Create a new user",
                "request": "POST /users\nContent-Type: application/json\n\n{\n  \"name\": \"John Doe\",\n  \"email\": \"john@example.com\",\n  \"age\": 30,\n  \"status\": \"active\"\n}",
                "response": {"id": 3, "name": "John Doe", "email": "john@example.com", "age": 30, "status": "active"}
            }
        ]
    )
    
    # GET /users/{id} - Get user
    builder.add_endpoint(
        path="/users/{id}",
        method=HttpMethod.GET,
        summary="Get user by ID",
        description="Retrieve a specific user by their ID",
        tags=["Users"],
        parameters=[
            Parameter("id", "integer", True, "User ID", example=1)
        ],
        responses=[
            Response(200, "User found", 
                schema={"$ref": "#/components/schemas/User"},
                example={"id": 1, "name": "John Doe", "email": "john@example.com", "age": 30, "status": "active"}
            ),
            Response(404, "User not found")
        ]
    )
    
    # DELETE /users/{id} - Delete user
    builder.add_endpoint(
        path="/users/{id}",
        method=HttpMethod.DELETE,
        summary="Delete user",
        description="Delete a user by ID",
        tags=["Admin"],
        parameters=[
            Parameter("id", "integer", True, "User ID", example=1)
        ],
        responses=[
            Response(204, "User deleted"),
            Response(404, "User not found"),
            Response(403, "Insufficient permissions")
        ],
        authentication_required=True,
        notes=[
            "This action cannot be undone",
            "Only admins can delete users"
        ]
    )
    
    return builder.build()


def test_documentation():
    """Test the documentation generation"""
    
    # Create documentation
    doc = create_sample_documentation()
    
    # Print in different formats
    print("=" * 60)
    print("API DOCUMENTATION EXAMPLES")
    print("=" * 60)
    
    # JSON
    print("\n1. JSON Format:")
    print("-" * 40)
    print(doc.to_json()[:500] + "...")
    
    # Markdown (first few lines)
    print("\n2. Markdown Format (first few lines):")
    print("-" * 40)
    markdown = doc.to_markdown()
    print("\n".join(markdown.split("\n")[:30]) + "...")
    
    # OpenAPI
    print("\n3. OpenAPI 3.0 Format (first few lines):")
    print("-" * 40)
    openapi = doc.to_openapi()
    print(json.dumps(openapi, indent=2)[:500] + "...")
    
    # Interactive display
    print("\n4. Interactive Display:")
    print("-" * 40)
    interactive = InteractiveAPIDoc(doc)
    interactive.display()
    
    # Save to files
    print("\n5. Saving to files:")
    print("-" * 40)
    
    # Save JSON
    with open("api_documentation.json", "w") as f:
        f.write(doc.to_json())
    print("✓ Saved JSON documentation to 'api_documentation.json'")
    
    # Save Markdown
    with open("api_documentation.md", "w") as f:
        f.write(doc.to_markdown())
    print("✓ Saved Markdown documentation to 'api_documentation.md'")
    
    # Save OpenAPI
    with open("openapi.json", "w") as f:
        json.dump(doc.to_openapi(), f, indent=2)
    print("✓ Saved OpenAPI specification to 'openapi.json'")
    
    # Save YAML
    with open("api_documentation.yaml", "w") as f:
        f.write(doc.to_yaml())
    print("✓ Saved YAML documentation to 'api_documentation.yaml'")
    
    print("\n" + "=" * 60)
    print("Documentation generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_documentation()
