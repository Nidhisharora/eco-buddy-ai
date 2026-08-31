"""
api_pagination.py
A module for handling paginated API responses with user-friendly features
"""

import requests
import json
from typing import Optional, Dict, Any, List, Union, Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import math
import time
from datetime import datetime


class PaginationStrategy(Enum):
    """Different pagination strategies used by APIs"""
    OFFSET_LIMIT = "offset_limit"  # Common: ?offset=0&limit=20
    PAGE_SIZE = "page_size"        # Common: ?page=1&size=20
    CURSOR = "cursor"              # Common: ?cursor=abc123
    LINK_HEADER = "link_header"    # GitHub-style Link headers
    NEXT_TOKEN = "next_token"      # Common: ?next_token=xyz
    CONTINUATION = "continuation"  # Common: ?continuation=def456


@dataclass
class PaginationInfo:
    """Information about pagination state"""
    total_items: Optional[int] = None
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    page_size: Optional[int] = None
    has_next: bool = False
    has_previous: bool = False
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    next_url: Optional[str] = None
    previous_url: Optional[str] = None
    strategy: PaginationStrategy = PaginationStrategy.OFFSET_LIMIT
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pagination info to dictionary"""
        return {
            "total_items": self.total_items,
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            "page_size": self.page_size,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
            "next_cursor": self.next_cursor,
            "previous_cursor": self.previous_cursor,
            "next_url": self.next_url,
            "previous_url": self.previous_url,
            "strategy": self.strategy.value
        }


@dataclass
class PaginatedResponse:
    """Standardized paginated API response"""
    data: List[Any]
    pagination: PaginationInfo
    metadata: Dict[str, Any] = field(default_factory=dict)
    status_code: Optional[int] = None
    request_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire response to dictionary"""
        return {
            "data": self.data,
            "pagination": self.pagination.to_dict(),
            "metadata": self.metadata,
            "status_code": self.status_code,
            "request_id": self.request_id,
            "timestamp": self.timestamp
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class PaginationHandler:
    """Handles pagination for API responses"""
    
    def __init__(self, default_page_size: int = 20, max_page_size: int = 100):
        """
        Initialize pagination handler
        
        Args:
            default_page_size: Default number of items per page
            max_page_size: Maximum allowed items per page
        """
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
    
    def parse_pagination(self, response: requests.Response) -> PaginationInfo:
        """
        Parse pagination information from API response
        
        Args:
            response: API response object
            
        Returns:
            PaginationInfo: Extracted pagination information
        """
        # Try to detect pagination strategy from response
        if 'Link' in response.headers:
            return self._parse_link_header(response.headers['Link'])
        
        # Try to parse from JSON body
        try:
            data = response.json()
            return self._parse_json_pagination(data, response.url)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try to parse from URL parameters
        return self._parse_url_pagination(response.url)
    
    def _parse_link_header(self, link_header: str) -> PaginationInfo:
        """Parse GitHub-style Link header"""
        pagination = PaginationInfo(strategy=PaginationStrategy.LINK_HEADER)
        
        links = link_header.split(',')
        for link in links:
            parts = link.split(';')
            if len(parts) != 2:
                continue
            
            url = parts[0].strip('<> ')
            rel = parts[1].strip().split('=')[1].strip('"')
            
            if rel == 'next':
                pagination.next_url = url
            elif rel == 'prev':
                pagination.previous_url = url
            elif rel == 'first':
                pass  # Not used for pagination state
            elif rel == 'last':
                pass  # Not used for pagination state
            
            pagination.has_next = pagination.next_url is not None
            pagination.has_previous = pagination.previous_url is not None
        
        return pagination
    
    def _parse_json_pagination(self, data: Dict[str, Any], url: str) -> PaginationInfo:
        """
        Parse pagination from JSON response body
        Supports various common formats
        """
        pagination = PaginationInfo()
        pagination.strategy = PaginationStrategy.OFFSET_LIMIT
        
        # Common pagination structures
        patterns = [
            # Structure: {"data": [], "pagination": {"page": 1, "total": 100, "per_page": 20}}
            ("pagination", "page", "total", "per_page"),
            # Structure: {"items": [], "total": 100, "page": 1, "limit": 20}
            ("", "page", "total", "limit"),
            # Structure: {"data": [], "meta": {"pagination": {"page": 1, "total": 100}}}
            ("meta", "pagination", "page", "total"),
            # Structure: {"items": [], "next_cursor": "abc", "prev_cursor": "def"}
            ("", "next_cursor", "prev_cursor"),
            # Structure: {"data": [], "nextToken": "abc", "prevToken": "def"}
            ("", "nextToken", "prevToken"),
        ]
        
        for pattern in patterns:
            if len(pattern) == 3:
                # Cursor pattern
                cursor_path, next_key, prev_key = pattern
                if cursor_path:
                    cursor_data = data.get(cursor_path, {})
                else:
                    cursor_data = data
                
                if next_key in cursor_data:
                    pagination.next_cursor = cursor_data.get(next_key)
                    pagination.has_next = True
                    pagination.strategy = PaginationStrategy.CURSOR
                if prev_key in cursor_data:
                    pagination.previous_cursor = cursor_data.get(prev_key)
                    pagination.has_previous = True
                
                break
            elif len(pattern) == 4:
                # Page/offset pattern
                pagination_path, page_key, total_key, per_page_key = pattern
                if pagination_path:
                    pag_data = data.get(pagination_path, {})
                else:
                    pag_data = data
                
                # For offset/limit style
                if page_key in pag_data:
                    if 'offset' in pag_data or 'limit' in pag_data:
                        # Offset/limit
                        offset = pag_data.get('offset', 0)
                        limit = pag_data.get('limit', self.default_page_size)
                        total = pag_data.get(total_key)
                        
                        pagination.current_page = (offset // limit) + 1 if limit > 0 else 1
                        pagination.page_size = limit
                        pagination.total_items = total
                        pagination.strategy = PaginationStrategy.OFFSET_LIMIT
                        
                        if total:
                            pagination.total_pages = (total + limit - 1) // limit
                            pagination.has_next = offset + limit < total
                            pagination.has_previous = offset > 0
                    else:
                        # Page/size
                        page = pag_data.get(page_key, 1)
                        size = pag_data.get(per_page_key, self.default_page_size)
                        total = pag_data.get(total_key)
                        
                        pagination.current_page = page
                        pagination.page_size = size
                        pagination.total_items = total
                        pagination.strategy = PaginationStrategy.PAGE_SIZE
                        
                        if total:
                            pagination.total_pages = (total + size - 1) // size
                            pagination.has_next = page < pagination.total_pages
                            pagination.has_previous = page > 1
                
                # Check for next_token style
                if 'next_token' in pag_data:
                    pagination.next_cursor = pag_data.get('next_token')
                    pagination.has_next = True
                    pagination.strategy = PaginationStrategy.NEXT_TOKEN
        
        return pagination
    
    def _parse_url_pagination(self, url: str) -> PaginationInfo:
        """Parse pagination parameters from URL"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        pagination = PaginationInfo()
        
        # Check for offset/limit
        if 'offset' in params or 'limit' in params:
            offset = int(params.get('offset', [0])[0])
            limit = int(params.get('limit', [self.default_page_size])[0])
            
            pagination.current_page = (offset // limit) + 1 if limit > 0 else 1
            pagination.page_size = limit
            pagination.strategy = PaginationStrategy.OFFSET_LIMIT
            pagination.has_previous = offset > 0
        
        # Check for page/size
        elif 'page' in params or 'size' in params:
            page = int(params.get('page', [1])[0])
            size = int(params.get('size', [self.default_page_size])[0])
            
            pagination.current_page = page
            pagination.page_size = size
            pagination.strategy = PaginationStrategy.PAGE_SIZE
            pagination.has_previous = page > 1
        
        # Check for cursor
        elif 'cursor' in params:
            pagination.next_cursor = params.get('cursor', [None])[0]
            pagination.strategy = PaginationStrategy.CURSOR
        
        # Check for next_token
        elif 'next_token' in params:
            pagination.next_cursor = params.get('next_token', [None])[0]
            pagination.strategy = PaginationStrategy.NEXT_TOKEN
        
        return pagination
    
    def build_pagination_url(self, base_url: str, params: Dict[str, Any]) -> str:
        """
        Build URL with pagination parameters
        
        Args:
            base_url: Base URL
            params: Pagination parameters
            
        Returns:
            str: URL with pagination parameters
        """
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Update with new params
        for key, value in params.items():
            if value is not None:
                query_params[key] = [str(value)]
            elif key in query_params:
                del query_params[key]
        
        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)
    
    def validate_pagination_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize pagination parameters
        
        Args:
            params: Pagination parameters
            
        Returns:
            Dict[str, Any]: Validated parameters
        """
        validated = params.copy()
        
        # Validate page size/limit
        if 'limit' in validated:
            validated['limit'] = min(
                max(1, int(validated['limit'])),
                self.max_page_size
            )
        elif 'size' in validated:
            validated['size'] = min(
                max(1, int(validated['size'])),
                self.max_page_size
            )
        
        # Validate page number
        if 'page' in validated:
            validated['page'] = max(1, int(validated['page']))
        
        # Validate offset
        if 'offset' in validated:
            validated['offset'] = max(0, int(validated['offset']))
        
        return validated


class PaginatedAPIClient:
    """API client with pagination support"""
    
    def __init__(
        self,
        base_url: str,
        default_page_size: int = 20,
        max_page_size: int = 100,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        self.base_url = base_url.rstrip('/')
        self.pagination_handler = PaginationHandler(default_page_size, max_page_size)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # Default headers
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        stream: bool = False
    ) -> PaginatedResponse:
        """
        Make a GET request with pagination support
        
        Args:
            endpoint: API endpoint
            params: Query parameters (including pagination)
            headers: Additional headers
            stream: Whether to stream the response
            
        Returns:
            PaginatedResponse: Standardized paginated response
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Validate pagination parameters
        if params:
            params = self.pagination_handler.validate_pagination_params(params)
        
        # Make request with retries
        response = self._make_request_with_retries('GET', url, params=params, headers=headers)
        
        # Parse pagination
        pagination = self.pagination_handler.parse_pagination(response)
        
        # Parse data
        try:
            data = response.json()
            
            # Extract data from common structures
            if 'data' in data:
                items = data['data']
            elif 'items' in data:
                items = data['items']
            elif 'results' in data:
                items = data['results']
            else:
                # Assume the entire response is the data
                items = data
            
            # If data is a dict and not a list, wrap it
            if isinstance(items, dict) and not isinstance(items, list):
                items = [items]
        except json.JSONDecodeError:
            items = []
        
        # Add metadata
        metadata = {}
        if 'metadata' in data:
            metadata = data['metadata']
        elif 'meta' in data:
            metadata = data['meta']
        
        return PaginatedResponse(
            data=items if isinstance(items, list) else [items],
            pagination=pagination,
            metadata=metadata,
            status_code=response.status_code,
            request_id=response.headers.get('X-Request-ID')
        )
    
    def get_all_pages(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_pages: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Fetch all pages of a paginated API
        
        Args:
            endpoint: API endpoint
            params: Initial query parameters
            headers: Additional headers
            max_pages: Maximum number of pages to fetch
            progress_callback: Callback function for progress updates
            
        Returns:
            List[Any]: All items from all pages
        """
        all_items = []
        current_params = params.copy() if params else {}
        page_count = 0
        
        while True:
            # Check max pages limit
            if max_pages and page_count >= max_pages:
                break
            
            # Get current page
            response = self.get_paginated(endpoint, current_params, headers)
            
            # Add items
            all_items.extend(response.data)
            page_count += 1
            
            # Call progress callback
            if progress_callback:
                total = response.pagination.total_items or len(response.data)
                progress_callback(len(all_items), total if total > 0 else len(response.data))
            
            # Check if there's a next page
            if not response.pagination.has_next:
                break
            
            # Update parameters for next page
            pagination = response.pagination
            
            if pagination.strategy == PaginationStrategy.LINK_HEADER:
                # Use next URL
                if pagination.next_url:
                    # Parse next URL to get parameters
                    parsed = urlparse(pagination.next_url)
                    next_params = parse_qs(parsed.query)
                    current_params = {k: v[0] if len(v) == 1 else v for k, v in next_params.items()}
                    continue
            
            # Handle different pagination strategies
            if pagination.strategy in [PaginationStrategy.OFFSET_LIMIT, PaginationStrategy.PAGE_SIZE]:
                if pagination.current_page is not None:
                    current_params['page'] = pagination.current_page + 1
                elif 'offset' in current_params:
                    current_params['offset'] = current_params.get('offset', 0) + current_params.get('limit', self.pagination_handler.default_page_size)
            
            elif pagination.strategy == PaginationStrategy.CURSOR:
                if pagination.next_cursor:
                    current_params['cursor'] = pagination.next_cursor
                else:
                    break
            
            elif pagination.strategy == PaginationStrategy.NEXT_TOKEN:
                if pagination.next_cursor:
                    current_params['next_token'] = pagination.next_cursor
                else:
                    break
            
            elif pagination.strategy == PaginationStrategy.CONTINUATION:
                if pagination.next_cursor:
                    current_params['continuation'] = pagination.next_cursor
                else:
                    break
            
            else:
                # Unknown strategy, break to avoid infinite loop
                break
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.1)
        
        return all_items
    
    def get_pages_iter(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_pages: Optional[int] = None
    ) -> Iterator[PaginatedResponse]:
        """
        Iterator for fetching pages one at a time
        
        Args:
            endpoint: API endpoint
            params: Initial query parameters
            headers: Additional headers
            max_pages: Maximum number of pages to iterate
            
        Yields:
            PaginatedResponse: Each page response
        """
        current_params = params.copy() if params else {}
        page_count = 0
        
        while True:
            # Check max pages limit
            if max_pages and page_count >= max_pages:
                break
            
            # Get current page
            response = self.get_paginated(endpoint, current_params, headers)
            page_count += 1
            
            yield response
            
            # Check if there's a next page
            if not response.pagination.has_next:
                break
            
            # Update parameters for next page
            pagination = response.pagination
            
            if pagination.strategy == PaginationStrategy.LINK_HEADER:
                if pagination.next_url:
                    parsed = urlparse(pagination.next_url)
                    next_params = parse_qs(parsed.query)
                    current_params = {k: v[0] if len(v) == 1 else v for k, v in next_params.items()}
                    continue
            
            # Handle different pagination strategies
            if pagination.strategy in [PaginationStrategy.OFFSET_LIMIT, PaginationStrategy.PAGE_SIZE]:
                if pagination.current_page is not None:
                    current_params['page'] = pagination.current_page + 1
                elif 'offset' in current_params:
                    current_params['offset'] = current_params.get('offset', 0) + current_params.get('limit', self.pagination_handler.default_page_size)
            
            elif pagination.strategy == PaginationStrategy.CURSOR:
                if pagination.next_cursor:
                    current_params['cursor'] = pagination.next_cursor
                else:
                    break
            
            elif pagination.strategy == PaginationStrategy.NEXT_TOKEN:
                if pagination.next_cursor:
                    current_params['next_token'] = pagination.next_cursor
                else:
                    break
            
            else:
                break
            
            time.sleep(0.1)
    
    def _make_request_with_retries(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """Make request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise
                
                # Don't retry on 4xx client errors (except rate limiting)
                if hasattr(e, 'response') and e.response:
                    if 400 <= e.response.status_code < 429:
                        raise
                    if e.response.status_code == 429 and 'Retry-After' in e.response.headers:
                        retry_after = int(e.response.headers.get('Retry-After', self.retry_delay))
                        time.sleep(retry_after)
                        continue
                
                # Exponential backoff
                time.sleep(self.retry_delay * (2 ** attempt))


class UserFriendlyPaginatedAPI:
    """Wrapper that combines pagination with user-friendly error messages"""
    
    def __init__(
        self,
        base_url: str,
        default_page_size: int = 20,
        max_page_size: int = 100
    ):
        self.client = PaginatedAPIClient(base_url, default_page_size, max_page_size)
        self.error_handler = None  # Can be set to use the APIErrorHandler from previous module
    
    def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> PaginatedResponse:
        """
        Get paginated response with error handling
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            headers: Additional headers
            
        Returns:
            PaginatedResponse: Paginated response
            
        Raises:
            Exception: With user-friendly error message if available
        """
        try:
            return self.client.get_paginated(endpoint, params, headers)
        except requests.exceptions.RequestException as e:
            # If error handler is available, use it
            if self.error_handler:
                error_obj = self.error_handler.handle_error(e)
                raise Exception(error_obj.message) from e
            raise
    
    def get_all_items(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Get all items with progress tracking and error handling
        """
        try:
            return self.client.get_all_pages(
                endpoint, params, 
                max_pages=max_pages,
                progress_callback=progress_callback
            )
        except requests.exceptions.RequestException as e:
            if self.error_handler:
                error_obj = self.error_handler.handle_error(e)
                raise Exception(error_obj.message) from e
            raise


# Example usage and tests
def test_pagination():
    """Test pagination functionality with mock data"""
    
    # Example 1: JSON Placeholder API (uses page/size)
    print("Example 1: Fetching posts with pagination")
    client = PaginatedAPIClient("https://jsonplaceholder.typicode.com")
    
    # Get first page
    response = client.get_paginated(
        "posts",
        params={"page": 1, "size": 5}
    )
    
    print(f"Page {response.pagination.current_page} of {response.pagination.total_pages}")
    print(f"Items on this page: {len(response.data)}")
    print(f"Total items: {response.pagination.total_items}")
    print(f"Has next: {response.pagination.has_next}")
    print("\nFirst few items:")
    for item in response.data[:3]:
        print(f"  - {item.get('title', 'No title')}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Fetch all pages
    print("Example 2: Fetching all pages")
    all_posts = client.get_all_pages(
        "posts",
        params={"size": 10},
        max_pages=3,  # Limit to 3 pages for demo
        progress_callback=lambda current, total: print(f"Fetched {current} of {total} items")
    )
    print(f"Total posts fetched: {len(all_posts)}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Using iterator
    print("Example 3: Iterating through pages")
    for i, page in enumerate(client.get_pages_iter(
        "posts",
        params={"size": 5},
        max_pages=2
    )):
        print(f"Page {i+1}: {len(page.data)} items")
        print(f"  Page info: {page.pagination.to_dict()}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Pagination info display
    print("Example 4: Complete pagination info")
    response = client.get_paginated("posts", params={"page": 2, "size": 5})
    pagination_dict = response.pagination.to_dict()
    print(json.dumps(pagination_dict, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Example 5: Building pagination URLs
    print("Example 5: Building pagination URLs")
    handler = PaginationHandler()
    url = handler.build_pagination_url(
        "https://api.example.com/users",
        {"page": 2, "size": 20}
    )
    print(f"Generated URL: {url}")


def test_mock_pagination():
    """Test with mock API that simulates different pagination strategies"""
    
    class MockAPIClient:
        """Mock client for testing"""
        
        def __init__(self):
            self.data = [{"id": i, "name": f"Item {i}"} for i in range(1, 101)]
        
        def get(self, url, params=None):
            """Mock GET request"""
            class MockResponse:
                def __init__(self, data, status_code=200, headers=None):
                    self._data = data
                    self.status_code = status_code
                    self.headers = headers or {}
                    self.text = json.dumps(data)
                
                def json(self):
                    return self._data
                
                def raise_for_status(self):
                    pass
            
            # Parse parameters
            page = int(params.get('page', 1)) if params else 1
            size = int(params.get('size', 10)) if params else 10
            
            # Calculate slice
            start = (page - 1) * size
            end = start + size
            items = self.data[start:end]
            total = len(self.data)
            
            # Build response
            response_data = {
                "data": items,
                "pagination": {
                    "page": page,
                    "per_page": size,
                    "total": total,
                    "total_pages": (total + size - 1) // size
                }
            }
            
            return MockResponse(response_data)
    
    print("Testing with mock API:")
    mock_client = MockAPIClient()
    
    # Create client that uses mock
    paginated_client = PaginatedAPIClient("http://mock.api")
    # Override session get with mock
    paginated_client.session.get = mock_client.get
    
    response = paginated_client.get_paginated(
        "items",
        params={"page": 2, "size": 10}
    )
    
    print(f"Page {response.pagination.current_page} of {response.pagination.total_pages}")
    print(f"Items: {[item['name'] for item in response.data]}")
    print(f"Pagination info: {response.pagination.to_dict()}")


if __name__ == "__main__":
    # Uncomment to test with real API
    # test_pagination()
    
    # Test with mock API
    test_mock_pagination()
