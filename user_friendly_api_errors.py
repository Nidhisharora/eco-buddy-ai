"""
user_friendly_api_errors.py
A module for handling API errors with user-friendly messages
"""

import requests
import json
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Categories of API errors for better user understanding"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    NETWORK = "network"
    VALIDATION = "validation"
    RESOURCE_NOT_FOUND = "resource_not_found"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class UserFriendlyError:
    """Structured user-friendly error response"""
    message: str
    category: ErrorCategory
    status_code: Optional[int] = None
    technical_details: Optional[str] = None
    action_items: Optional[list] = None
    retry_after: Optional[int] = None
    resource_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format"""
        return {
            "error": {
                "message": self.message,
                "category": self.category.value,
                "status_code": self.status_code,
                "technical_details": self.technical_details,
                "action_items": self.action_items,
                "retry_after": self.retry_after,
                "resource_id": self.resource_id
            }
        }


class APIErrorHandler:
    """Handles API errors and converts them to user-friendly messages"""
    
    # Common error messages mapped to user-friendly versions
    ERROR_MESSAGES = {
        400: {
            "default": "The request was invalid. Please check your input and try again.",
            "validation": "Some fields in your request need attention. Please review the highlighted fields.",
            "bad_syntax": "The request format is incorrect. Please check the API documentation.",
        },
        401: {
            "default": "Authentication is required to access this resource. Please log in.",
            "expired": "Your session has expired. Please log in again.",
            "invalid_token": "Your authentication token is invalid. Please log in again.",
            "missing_token": "Authentication token is missing. Please include your API key.",
        },
        403: {
            "default": "You don't have permission to access this resource.",
            "forbidden": "You don't have sufficient permissions to perform this action.",
            "account_locked": "Your account has been locked. Please contact support.",
            "ip_blocked": "This IP address has been blocked. Please contact support.",
        },
        404: {
            "default": "The requested resource could not be found.",
            "user_not_found": "User account not found. Please check the user ID or email.",
            "product_not_found": "Product not found. It may have been removed.",
            "endpoint_not_found": "The API endpoint you're trying to access doesn't exist.",
        },
        429: {
            "default": "You've made too many requests. Please slow down.",
            "rate_limit": "Rate limit exceeded. Please wait before making more requests.",
            "daily_limit": "Daily request limit reached. Please try again tomorrow.",
        },
        500: {
            "default": "Something went wrong on our server. We're working on it.",
            "service_unavailable": "The service is currently unavailable. Please try again later.",
            "database_error": "There was a database issue. Our team has been notified.",
            "third_party_error": "A third-party service is experiencing issues. Please try again later.",
        },
        502: {
            "default": "The service is temporarily unavailable. Please try again later.",
        },
        503: {
            "default": "The service is currently undergoing maintenance. Please try again later.",
            "overloaded": "The service is experiencing high load. Please try again later.",
        },
        504: {
            "default": "The request timed out. Please try again later.",
        },
    }
    
    # Action items for different error categories
    ACTION_ITEMS = {
        ErrorCategory.AUTHENTICATION: [
            "Log in to your account",
            "Check if your API key is valid",
            "Contact support if you continue to have issues"
        ],
        ErrorCategory.AUTHORIZATION: [
            "Contact your administrator to request access",
            "Check if you have the correct permissions",
            "Verify you're using the right account"
        ],
        ErrorCategory.RATE_LIMIT: [
            "Wait a moment before making another request",
            "Check the Retry-After header for timing",
            "Consider upgrading your plan for higher limits"
        ],
        ErrorCategory.RESOURCE_NOT_FOUND: [
            "Verify the resource ID or name is correct",
            "Check if the resource still exists",
            "Search for the resource using different parameters"
        ],
        ErrorCategory.SERVER_ERROR: [
            "Try again in a few minutes",
            "Check our status page for service updates",
            "Contact support if the issue persists"
        ],
        ErrorCategory.NETWORK: [
            "Check your internet connection",
            "Verify the API endpoint URL",
            "Check if the API server is reachable"
        ],
        ErrorCategory.VALIDATION: [
            "Review all required fields",
            "Check field format requirements",
            "Verify data types (strings, numbers, etc.)"
        ],
        ErrorCategory.TIMEOUT: [
            "Try sending a smaller request",
            "Increase your timeout settings",
            "Try again when the service is less busy"
        ],
    }
    
    @classmethod
    def handle_error(cls, error: Union[Exception, requests.Response]) -> UserFriendlyError:
        """
        Handle any API error and return a user-friendly message
        
        Args:
            error: Either an exception or a Response object
            
        Returns:
            UserFriendlyError: Structured error with friendly message
        """
        if isinstance(error, requests.Response):
            return cls._handle_response_error(error)
        elif isinstance(error, requests.RequestException):
            return cls._handle_network_error(error)
        else:
            return cls._handle_general_error(error)
    
    @classmethod
    def _handle_response_error(cls, response: requests.Response) -> UserFriendlyError:
        """Handle HTTP response errors"""
        status_code = response.status_code
        category = cls._get_error_category(status_code)
        
        # Try to get error details from response body
        error_body = cls._parse_error_body(response)
        
        # Generate user-friendly message
        friendly_message = cls._get_friendly_message(status_code, error_body)
        
        # Get action items
        action_items = cls.ACTION_ITEMS.get(category, ["Please try again or contact support"])
        
        # Extract any relevant technical details
        technical_details = cls._get_technical_details(response, error_body)
        
        # Get retry-after if available
        retry_after = cls._get_retry_after(response)
        
        # Check for specific resource IDs in error
        resource_id = cls._extract_resource_id(error_body)
        
        return UserFriendlyError(
            message=friendly_message,
            category=category,
            status_code=status_code,
            technical_details=technical_details,
            action_items=action_items,
            retry_after=retry_after,
            resource_id=resource_id
        )
    
    @classmethod
    def _handle_network_error(cls, error: requests.RequestException) -> UserFriendlyError:
        """Handle network-related errors"""
        category = ErrorCategory.NETWORK
        
        if isinstance(error, requests.Timeout):
            category = ErrorCategory.TIMEOUT
            message = "The request is taking too long to complete. Please try again."
        elif isinstance(error, requests.ConnectionError):
            message = "Unable to connect to the server. Please check your internet connection."
        elif isinstance(error, requests.TooManyRedirects):
            message = "Too many redirects. The server configuration may be incorrect."
        else:
            message = "A network error occurred. Please check your connection and try again."
        
        return UserFriendlyError(
            message=message,
            category=category,
            technical_details=str(error),
            action_items=cls.ACTION_ITEMS.get(category, ["Check your network connection and try again"])
        )
    
    @classmethod
    def _handle_general_error(cls, error: Exception) -> UserFriendlyError:
        """Handle general exceptions"""
        return UserFriendlyError(
            message="An unexpected error occurred. Please try again or contact support.",
            category=ErrorCategory.UNKNOWN,
            technical_details=str(error),
            action_items=["Try again", "Contact support if the issue persists"]
        )
    
    @classmethod
    def _get_error_category(cls, status_code: int) -> ErrorCategory:
        """Determine error category based on status code"""
        if status_code in (401,):
            return ErrorCategory.AUTHENTICATION
        elif status_code in (403,):
            return ErrorCategory.AUTHORIZATION
        elif status_code in (429,):
            return ErrorCategory.RATE_LIMIT
        elif status_code in (404,):
            return ErrorCategory.RESOURCE_NOT_FOUND
        elif 400 <= status_code < 500:
            return ErrorCategory.VALIDATION
        elif 500 <= status_code < 600:
            return ErrorCategory.SERVER_ERROR
        else:
            return ErrorCategory.UNKNOWN
    
    @classmethod
    def _parse_error_body(cls, response: requests.Response) -> Dict[str, Any]:
        """Parse error response body if available"""
        try:
            if response.text:
                return response.json()
        except json.JSONDecodeError:
            # If response is not JSON, return text as is
            return {"raw": response.text}
        return {}
    
    @classmethod
    def _get_friendly_message(cls, status_code: int, error_body: Dict[str, Any]) -> str:
        """Get user-friendly message for the error"""
        # Check for specific error type in body
        error_type = error_body.get("error", {}).get("type", "")
        error_message = error_body.get("error", {}).get("message", "")
        
        # Map specific error types to friendly messages
        friendly_messages = cls.ERROR_MESSAGES.get(status_code, {})
        
        # Try to find a specific message
        for key, message in friendly_messages.items():
            if key != "default" and key in error_type.lower():
                return message
        
        # Check for common patterns in error message
        if status_code == 401:
            if "expired" in error_message.lower():
                return friendly_messages.get("expired", friendly_messages["default"])
            elif "invalid" in error_message.lower():
                return friendly_messages.get("invalid_token", friendly_messages["default"])
        
        # Return default message for this status code
        return friendly_messages.get("default", f"An error occurred (HTTP {status_code}).")
    
    @classmethod
    def _get_technical_details(cls, response: requests.Response, error_body: Dict[str, Any]) -> Optional[str]:
        """Extract technical details for debugging"""
        details = []
        
        # Add status code
        details.append(f"Status Code: {response.status_code}")
        
        # Add response headers that might be useful
        if 'X-Request-ID' in response.headers:
            details.append(f"Request ID: {response.headers['X-Request-ID']}")
        if 'X-RateLimit-Reset' in response.headers:
            details.append(f"Rate Limit Reset: {response.headers['X-RateLimit-Reset']}")
        
        # Add error body if available
        if error_body:
            details.append(f"Error Details: {json.dumps(error_body, indent=2)}")
        
        return "\n".join(details) if details else None
    
    @classmethod
    def _get_retry_after(cls, response: requests.Response) -> Optional[int]:
        """Extract retry-after header if available"""
        if 'Retry-After' in response.headers:
            try:
                return int(response.headers['Retry-After'])
            except ValueError:
                # If it's a date, we'd need to parse it, but for simplicity we return None
                return None
        return None
    
    @classmethod
    def _extract_resource_id(cls, error_body: Dict[str, Any]) -> Optional[str]:
        """Extract resource ID from error body if available"""
        # Common patterns in error responses
        paths = [
            "error.resource_id",
            "resource.id",
            "id",
            "data.id"
        ]
        
        for path in paths:
            parts = path.split(".")
            value = error_body
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    break
            else:
                if value and isinstance(value, str):
                    return value
        
        return None


class APIErrorPrinter:
    """Utility for printing user-friendly error messages"""
    
    @staticmethod
    def print_error(error: Union[Exception, UserFriendlyError, requests.Response]):
        """Print a user-friendly error message"""
        if isinstance(error, UserFriendlyError):
            error_obj = error
        else:
            error_obj = APIErrorHandler.handle_error(error)
        
        # Color codes for terminal output
        RED = '\033[91m'
        YELLOW = '\033[93m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        RESET = '\033[0m'
        
        print(f"\n{RED}❌ Error{RESET}")
        print(f"{RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        print(f"{YELLOW}Message:{RESET} {error_obj.message}")
        
        if error_obj.category:
            print(f"{BLUE}Category:{RESET} {error_obj.category.value}")
        
        if error_obj.status_code:
            print(f"{BLUE}Status:{RESET} {error_obj.status_code}")
        
        if error_obj.retry_after:
            print(f"{BLUE}Try again in:{RESET} {error_obj.retry_after} seconds")
        
        if error_obj.resource_id:
            print(f"{BLUE}Resource ID:{RESET} {error_obj.resource_id}")
        
        if error_obj.action_items:
            print(f"\n{GREEN}Suggested actions:{RESET}")
            for item in error_obj.action_items:
                print(f"  • {item}")
        
        if error_obj.technical_details:
            print(f"\n{YELLOW}Technical details:{RESET}")
            print(f"  {error_obj.technical_details}")
        
        print(f"{RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")


# Example usage and test functions
def test_api_error_handling():
    """Test the API error handling with various scenarios"""
    
    class MockResponse:
        def __init__(self, status_code, json_data=None, headers=None, text=""):
            self.status_code = status_code
            self._json_data = json_data
            self.headers = headers or {}
            self.text = text if not json_data else ""
        
        def json(self):
            return self._json_data
        
        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")
    
    # Test 1: 404 Not Found
    print("Test 1: 404 Not Found")
    response = MockResponse(404, {"error": {"message": "User not found"}})
    error = APIErrorHandler.handle_error(response)
    APIErrorPrinter.print_error(error)
    print("\n" + "="*50 + "\n")
    
    # Test 2: 401 Unauthorized
    print("Test 2: 401 Unauthorized")
    response = MockResponse(401, {"error": {"type": "expired"}})
    error = APIErrorHandler.handle_error(response)
    APIErrorPrinter.print_error(error)
    print("\n" + "="*50 + "\n")
    
    # Test 3: 429 Rate Limit
    print("Test 3: 429 Rate Limit")
    response = MockResponse(429, {"error": {"message": "Too many requests"}}, 
                           headers={"Retry-After": "60"})
    error = APIErrorHandler.handle_error(response)
    APIErrorPrinter.print_error(error)
    print("\n" + "="*50 + "\n")
    
    # Test 4: Network Error
    print("Test 4: Network Error")
    error = APIErrorHandler.handle_error(requests.exceptions.ConnectionError("Connection refused"))
    APIErrorPrinter.print_error(error)
    print("\n" + "="*50 + "\n")
    
    # Test 5: Validation Error
    print("Test 5: Validation Error")
    response = MockResponse(400, {"error": {"type": "validation", "message": "Invalid email format"}})
    error = APIErrorHandler.handle_error(response)
    APIErrorPrinter.print_error(error)
    print("\n" + "="*50 + "\n")
    
    # Test 6: Timeout Error
    print("Test 6: Timeout Error")
    error = APIErrorHandler.handle_error(requests.exceptions.Timeout("Request timed out"))
    APIErrorPrinter.print_error(error)
    print("\n" + "="*50 + "\n")
    
    # Test 7: Complete error object
    print("Test 7: Complete Error Object")
    error_obj = UserFriendlyError(
        message="Failed to fetch user data",
        category=ErrorCategory.RESOURCE_NOT_FOUND,
        status_code=404,
        technical_details="User ID: 12345 not found in database",
        action_items=["Verify user ID", "Check if user exists", "Try searching by email"],
        resource_id="12345"
    )
    APIErrorPrinter.print_error(error_obj)


if __name__ == "__main__":
    test_api_error_handling()
