"""
api_search_filter.py
A module for handling search and filtering in API responses with pagination
"""

import requests
import json
from typing import Optional, Dict, Any, List, Union, Callable, Iterator, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import math
import time
from datetime import datetime, date
import re
from abc import ABC, abstractmethod


class FilterOperator(Enum):
    """Operators for filtering"""
    EQ = "eq"          # Equal to
    NE = "ne"          # Not equal to
    GT = "gt"          # Greater than
    GTE = "gte"        # Greater than or equal to
    LT = "lt"          # Less than
    LTE = "lte"        # Less than or equal to
    IN = "in"          # In a list
    NIN = "nin"        # Not in a list
    LIKE = "like"      # Contains substring
    STARTSWITH = "sw"  # Starts with
    ENDSWITH = "ew"    # Ends with
    BETWEEN = "between" # Between two values
    IS_NULL = "null"    # Is null
    IS_NOT_NULL = "nn"  # Is not null


class SortOrder(Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


@dataclass
class FilterCondition:
    """A single filter condition"""
    field: str
    operator: FilterOperator
    value: Any
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value
        }


@dataclass
class SearchCriteria:
    """Complete search criteria"""
    filters: List[FilterCondition] = field(default_factory=list)
    sort_by: Optional[str] = None
    sort_order: SortOrder = SortOrder.ASC
    search_text: Optional[str] = None
    search_fields: Optional[List[str]] = None
    page: int = 1
    page_size: int = 20
    include_total: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "filters": [f.to_dict() for f in self.filters],
            "sort": {
                "field": self.sort_by,
                "order": self.sort_order.value
            } if self.sort_by else None,
            "search": {
                "text": self.search_text,
                "fields": self.search_fields
            } if self.search_text else None,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size
            },
            "include_total": self.include_total
        }


@dataclass
class SearchResult:
    """Search result with metadata"""
    data: List[Any]
    total: Optional[int] = None
    page: int = 1
    page_size: int = 20
    total_pages: Optional[int] = None
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    query_time_ms: Optional[float] = None
    applied_filters: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "data": self.data,
            "pagination": {
                "page": self.page,
                "page_size": self.page_size,
                "total": self.total,
                "total_pages": self.total_pages
            },
            "facets": self.facets,
            "query_time_ms": self.query_time_ms,
            "applied_filters": self.applied_filters
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class SearchFilterBuilder:
    """Builder for creating search and filter criteria"""
    
    def __init__(self):
        self.criteria = SearchCriteria()
    
    def add_filter(self, field: str, operator: FilterOperator, value: Any) -> 'SearchFilterBuilder':
        """Add a filter condition"""
        self.criteria.filters.append(FilterCondition(field, operator, value))
        return self
    
    def add_eq(self, field: str, value: Any) -> 'SearchFilterBuilder':
        """Add equality filter"""
        return self.add_filter(field, FilterOperator.EQ, value)
    
    def add_ne(self, field: str, value: Any) -> 'SearchFilterBuilder':
        """Add not equal filter"""
        return self.add_filter(field, FilterOperator.NE, value)
    
    def add_gt(self, field: str, value: Any) -> 'SearchFilterBuilder':
        """Add greater than filter"""
        return self.add_filter(field, FilterOperator.GT, value)
    
    def add_gte(self, field: str, value: Any) -> 'SearchFilterBuilder':
        """Add greater than or equal filter"""
        return self.add_filter(field, FilterOperator.GTE, value)
    
    def add_lt(self, field: str, value: Any) -> 'SearchFilterBuilder':
        """Add less than filter"""
        return self.add_filter(field, FilterOperator.LT, value)
    
    def add_lte(self, field: str, value: Any) -> 'SearchFilterBuilder':
        """Add less than or equal filter"""
        return self.add_filter(field, FilterOperator.LTE, value)
    
    def add_in(self, field: str, values: List[Any]) -> 'SearchFilterBuilder':
        """Add in list filter"""
        return self.add_filter(field, FilterOperator.IN, values)
    
    def add_between(self, field: str, start: Any, end: Any) -> 'SearchFilterBuilder':
        """Add between filter"""
        return self.add_filter(field, FilterOperator.BETWEEN, [start, end])
    
    def add_like(self, field: str, value: str) -> 'SearchFilterBuilder':
        """Add contains filter"""
        return self.add_filter(field, FilterOperator.LIKE, value)
    
    def add_starts_with(self, field: str, value: str) -> 'SearchFilterBuilder':
        """Add starts with filter"""
        return self.add_filter(field, FilterOperator.STARTSWITH, value)
    
    def add_ends_with(self, field: str, value: str) -> 'SearchFilterBuilder':
        """Add ends with filter"""
        return self.add_filter(field, FilterOperator.ENDSWITH, value)
    
    def add_is_null(self, field: str) -> 'SearchFilterBuilder':
        """Add is null filter"""
        return self.add_filter(field, FilterOperator.IS_NULL, None)
    
    def add_is_not_null(self, field: str) -> 'SearchFilterBuilder':
        """Add is not null filter"""
        return self.add_filter(field, FilterOperator.IS_NOT_NULL, None)
    
    def set_sort(self, field: str, order: SortOrder = SortOrder.ASC) -> 'SearchFilterBuilder':
        """Set sort field and order"""
        self.criteria.sort_by = field
        self.criteria.sort_order = order
        return self
    
    def set_search(self, text: str, fields: Optional[List[str]] = None) -> 'SearchFilterBuilder':
        """Set search text and fields"""
        self.criteria.search_text = text
        self.criteria.search_fields = fields
        return self
    
    def set_pagination(self, page: int = 1, page_size: int = 20) -> 'SearchFilterBuilder':
        """Set pagination parameters"""
        self.criteria.page = page
        self.criteria.page_size = page_size
        return self
    
    def include_total(self, include: bool = True) -> 'SearchFilterBuilder':
        """Include total count in response"""
        self.criteria.include_total = include
        return self
    
    def build(self) -> SearchCriteria:
        """Build the search criteria"""
        return self.criteria


class QueryParser:
    """Parse query strings into search criteria"""
    
    @staticmethod
    def parse_query(query_string: str) -> SearchCriteria:
        """
        Parse a query string into search criteria
        
        Examples:
            "name:John age:>30" -> filter name=John and age>30
            "status:active sort:name desc" -> filter status=active, sort by name descending
            "search:hello" -> text search for hello
        """
        builder = SearchFilterBuilder()
        
        # Parse tokens
        tokens = query_string.split()
        current_field = None
        current_operator = None
        current_value = None
        
        for token in tokens:
            # Check for field:value pattern
            if ':' in token:
                field, value = token.split(':', 1)
                
                # Check for operators
                if field.startswith('sort'):
                    # Sort: sort:field order
                    parts = value.split()
                    if len(parts) >= 1:
                        builder.set_sort(parts[0])
                        if len(parts) >= 2 and parts[1].lower() in ['desc', 'descending']:
                            builder.set_sort(parts[0], SortOrder.DESC)
                elif field == 'search':
                    # Full text search
                    builder.set_search(value)
                else:
                    # Regular filter
                    # Check for operator in field name
                    for op in FilterOperator:
                        if field.endswith(f'_{op.value}'):
                            actual_field = field[:-len(f'_{op.value}')]
                            builder.add_filter(actual_field, op, value)
                            break
                    else:
                        # Default to equality
                        builder.add_eq(field, value)
            else:
                # Could be part of a multi-word value or search text
                if current_field:
                    current_value = f"{current_value} {token}" if current_value else token
        
        return builder.build()
    
    @staticmethod
    def parse_filters(filter_params: Dict[str, Any]) -> List[FilterCondition]:
        """
        Parse filter parameters from a dictionary
        
        Supports formats:
        - {"field": "value"} -> equality
        - {"field__gt": "value"} -> greater than
        - {"field__in": ["value1", "value2"]} -> in list
        """
        filters = []
        operator_map = {
            "__gt": FilterOperator.GT,
            "__gte": FilterOperator.GTE,
            "__lt": FilterOperator.LT,
            "__lte": FilterOperator.LTE,
            "__ne": FilterOperator.NE,
            "__in": FilterOperator.IN,
            "__nin": FilterOperator.NIN,
            "__like": FilterOperator.LIKE,
            "__sw": FilterOperator.STARTSWITH,
            "__ew": FilterOperator.ENDSWITH,
            "__between": FilterOperator.BETWEEN,
            "__null": FilterOperator.IS_NULL,
            "__nn": FilterOperator.IS_NOT_NULL,
        }
        
        for key, value in filter_params.items():
            operator = FilterOperator.EQ
            field = key
            
            # Check for operator suffix
            for suffix, op in operator_map.items():
                if key.endswith(suffix):
                    field = key[:-len(suffix)]
                    operator = op
                    break
            
            filters.append(FilterCondition(field, operator, value))
        
        return filters


class SearchFilterHandler:
    """Handles search and filtering for API requests"""
    
    def __init__(self, max_page_size: int = 100, default_page_size: int = 20):
        self.max_page_size = max_page_size
        self.default_page_size = default_page_size
    
    def build_query_params(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """
        Build query parameters from search criteria
        
        Returns:
            Dict[str, Any]: Query parameters for API request
        """
        params = {}
        
        # Pagination
        params['page'] = criteria.page
        params['size'] = min(criteria.page_size, self.max_page_size)
        
        # Sorting
        if criteria.sort_by:
            params['sort'] = f"{criteria.sort_by}:{criteria.sort_order.value}"
        
        # Search
        if criteria.search_text:
            params['q'] = criteria.search_text
            if criteria.search_fields:
                params['search_fields'] = ','.join(criteria.search_fields)
        
        # Filters - convert to API-specific format
        if criteria.filters:
            filter_params = self._encode_filters(criteria.filters)
            params.update(filter_params)
        
        # Include total
        if criteria.include_total:
            params['include_total'] = 'true'
        
        return params
    
    def _encode_filters(self, filters: List[FilterCondition]) -> Dict[str, Any]:
        """
        Encode filters for API request
        
        This can be overridden for different API formats
        """
        params = {}
        for filter_cond in filters:
            key = filter_cond.field
            
            # Add operator suffix if not equality
            if filter_cond.operator != FilterOperator.EQ:
                key += f"__{filter_cond.operator.value}"
            
            # Handle special value types
            if filter_cond.operator in [FilterOperator.IN, FilterOperator.NIN]:
                # Convert list to comma-separated string
                if isinstance(filter_cond.value, list):
                    params[key] = ','.join(str(v) for v in filter_cond.value)
                else:
                    params[key] = str(filter_cond.value)
            elif filter_cond.operator == FilterOperator.BETWEEN:
                # Between expects list of [start, end]
                if isinstance(filter_cond.value, list) and len(filter_cond.value) == 2:
                    params[f"{key}__between_start"] = filter_cond.value[0]
                    params[f"{key}__between_end"] = filter_cond.value[1]
                else:
                    params[key] = str(filter_cond.value)
            else:
                params[key] = str(filter_cond.value)
        
        return params
    
    def parse_response(self, response_data: Dict[str, Any]) -> SearchResult:
        """
        Parse API response into SearchResult
        
        Supports various response formats
        """
        # Extract data
        if 'data' in response_data:
            data = response_data['data']
        elif 'items' in response_data:
            data = response_data['items']
        elif 'results' in response_data:
            data = response_data['results']
        else:
            data = response_data
        
        # Ensure data is a list
        if isinstance(data, dict) and not isinstance(data, list):
            data = [data]
        
        # Extract pagination info
        page = 1
        page_size = len(data)
        total = None
        total_pages = None
        
        if 'pagination' in response_data:
            pagination = response_data['pagination']
            page = pagination.get('page', 1)
            page_size = pagination.get('page_size', pagination.get('size', len(data)))
            total = pagination.get('total')
            total_pages = pagination.get('total_pages')
        elif 'meta' in response_data:
            meta = response_data['meta']
            page = meta.get('page', 1)
            page_size = meta.get('page_size', meta.get('size', len(data)))
            total = meta.get('total')
            total_pages = meta.get('total_pages')
        
        # Extract facets
        facets = response_data.get('facets', {})
        
        # Extract query time
        query_time_ms = response_data.get('query_time_ms')
        
        # Extract applied filters
        applied_filters = response_data.get('applied_filters', [])
        
        return SearchResult(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            facets=facets,
            query_time_ms=query_time_ms,
            applied_filters=applied_filters
        )


class SearchableAPIClient:
    """API client with search and filtering capabilities"""
    
    def __init__(
        self,
        base_url: str,
        default_page_size: int = 20,
        max_page_size: int = 100,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.search_handler = SearchFilterHandler(max_page_size, default_page_size)
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def search(
        self,
        endpoint: str,
        criteria: Union[SearchCriteria, Dict[str, Any], str],
        headers: Optional[Dict[str, str]] = None
    ) -> SearchResult:
        """
        Perform a search with criteria
        
        Args:
            endpoint: API endpoint
            criteria: Search criteria (SearchCriteria, dict, or query string)
            headers: Additional headers
            
        Returns:
            SearchResult: Search results with metadata
        """
        # Parse criteria
        if isinstance(criteria, str):
            criteria = QueryParser.parse_query(criteria)
        elif isinstance(criteria, dict):
            builder = SearchFilterBuilder()
            
            # Extract pagination
            page = criteria.get('page', 1)
            page_size = criteria.get('page_size', 20)
            builder.set_pagination(page, page_size)
            
            # Extract sort
            if 'sort_by' in criteria:
                sort_order = criteria.get('sort_order', 'asc')
                order = SortOrder.ASC if sort_order.lower() == 'asc' else SortOrder.DESC
                builder.set_sort(criteria['sort_by'], order)
            
            # Extract search
            if 'search' in criteria:
                search_fields = criteria.get('search_fields')
                builder.set_search(criteria['search'], search_fields)
            
            # Extract filters
            if 'filters' in criteria:
                for filter_dict in criteria['filters']:
                    builder.add_filter(
                        filter_dict['field'],
                        FilterOperator(filter_dict['operator']),
                        filter_dict['value']
                    )
            
            criteria = builder.build()
        
        # Build query parameters
        params = self.search_handler.build_query_params(criteria)
        
        # Make request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self._make_request('GET', url, params=params, headers=headers)
        
        # Parse response
        try:
            data = response.json()
            return self.search_handler.parse_response(data)
        except json.JSONDecodeError:
            return SearchResult(data=[], total=0, page=1, page_size=0)
    
    def search_all(
        self,
        endpoint: str,
        criteria: Union[SearchCriteria, Dict[str, Any], str],
        max_pages: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Get all results from a search
        
        Args:
            endpoint: API endpoint
            criteria: Search criteria
            max_pages: Maximum pages to fetch
            progress_callback: Progress callback
            
        Returns:
            List[Any]: All items
        """
        if isinstance(criteria, str):
            criteria = QueryParser.parse_query(criteria)
        elif isinstance(criteria, dict):
            builder = SearchFilterBuilder()
            criteria = self._dict_to_criteria(criteria, builder)
        
        all_items = []
        current_criteria = criteria
        page_count = 0
        
        while True:
            if max_pages and page_count >= max_pages:
                break
            
            result = self.search(endpoint, current_criteria)
            all_items.extend(result.data)
            page_count += 1
            
            if progress_callback:
                progress_callback(len(all_items), result.total or len(result.data))
            
            # Check if there are more pages
            if result.total_pages and result.page >= result.total_pages:
                break
            elif not result.data:
                break
            
            # Update to next page
            current_criteria = SearchCriteria(
                filters=current_criteria.filters,
                sort_by=current_criteria.sort_by,
                sort_order=current_criteria.sort_order,
                search_text=current_criteria.search_text,
                search_fields=current_criteria.search_fields,
                page=result.page + 1,
                page_size=current_criteria.page_size,
                include_total=current_criteria.include_total
            )
            
            time.sleep(0.1)
        
        return all_items
    
    def _dict_to_criteria(self, criteria_dict: Dict[str, Any], builder: SearchFilterBuilder) -> SearchCriteria:
        """Convert dictionary to SearchCriteria"""
        # Pagination
        page = criteria_dict.get('page', 1)
        page_size = criteria_dict.get('page_size', 20)
        builder.set_pagination(page, page_size)
        
        # Sort
        if 'sort_by' in criteria_dict:
            sort_order = criteria_dict.get('sort_order', 'asc')
            order = SortOrder.ASC if sort_order.lower() == 'asc' else SortOrder.DESC
            builder.set_sort(criteria_dict['sort_by'], order)
        
        # Search
        if 'search' in criteria_dict:
            search_fields = criteria_dict.get('search_fields')
            builder.set_search(criteria_dict['search'], search_fields)
        
        # Filters
        if 'filters' in criteria_dict:
            for filter_dict in criteria_dict['filters']:
                if isinstance(filter_dict, dict):
                    builder.add_filter(
                        filter_dict['field'],
                        FilterOperator(filter_dict['operator']),
                        filter_dict['value']
                    )
        
        return builder.build()
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
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
                time.sleep(2 ** attempt)


class AdvancedSearchBuilder:
    """Advanced builder with fluent interface for complex searches"""
    
    def __init__(self):
        self.builder = SearchFilterBuilder()
        self.facet_fields = []
        self.aggregations = {}
        self.highlight_fields = []
        self.query_timeout_ms = None
    
    def where(self, field: str, operator: FilterOperator, value: Any) -> 'AdvancedSearchBuilder':
        """Add a filter condition"""
        self.builder.add_filter(field, operator, value)
        return self
    
    def where_eq(self, field: str, value: Any) -> 'AdvancedSearchBuilder':
        """Add equality filter"""
        self.builder.add_eq(field, value)
        return self
    
    def where_gt(self, field: str, value: Any) -> 'AdvancedSearchBuilder':
        """Add greater than filter"""
        self.builder.add_gt(field, value)
        return self
    
    def where_between(self, field: str, start: Any, end: Any) -> 'AdvancedSearchBuilder':
        """Add between filter"""
        self.builder.add_between(field, start, end)
        return self
    
    def where_like(self, field: str, value: str) -> 'AdvancedSearchBuilder':
        """Add contains filter"""
        self.builder.add_like(field, value)
        return self
    
    def search_text(self, text: str, fields: Optional[List[str]] = None) -> 'AdvancedSearchBuilder':
        """Set search text"""
        self.builder.set_search(text, fields)
        return self
    
    def sort_by(self, field: str, order: SortOrder = SortOrder.ASC) -> 'AdvancedSearchBuilder':
        """Set sort field"""
        self.builder.set_sort(field, order)
        return self
    
    def page(self, page: int, size: int = 20) -> 'AdvancedSearchBuilder':
        """Set pagination"""
        self.builder.set_pagination(page, size)
        return self
    
    def facet(self, *fields: str) -> 'AdvancedSearchBuilder':
        """Add facet fields"""
        self.facet_fields.extend(fields)
        return self
    
    def highlight(self, *fields: str) -> 'AdvancedSearchBuilder':
        """Add highlight fields"""
        self.highlight_fields.extend(fields)
        return self
    
    def aggregate(self, field: str, aggregation_type: str, alias: Optional[str] = None) -> 'AdvancedSearchBuilder':
        """Add aggregation"""
        if alias is None:
            alias = f"{field}_{aggregation_type}"
        self.aggregations[alias] = {"field": field, "type": aggregation_type}
        return self
    
    def timeout(self, ms: int) -> 'AdvancedSearchBuilder':
        """Set query timeout in milliseconds"""
        self.query_timeout_ms = ms
        return self
    
    def build(self) -> SearchCriteria:
        """Build search criteria"""
        criteria = self.builder.build()
        # Additional properties can be stored for advanced features
        return criteria


class FilterValidator:
    """Validates filter values and operators"""
    
    @staticmethod
    def validate_filter(filter_cond: FilterCondition) -> Tuple[bool, Optional[str]]:
        """
        Validate a filter condition
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check if field is valid (customize as needed)
        invalid_fields = ['__proto__', 'constructor', 'prototype']
        if filter_cond.field in invalid_fields:
            return False, f"Invalid field name: {filter_cond.field}"
        
        # Validate value based on operator
        if filter_cond.operator in [FilterOperator.IN, FilterOperator.NIN]:
            if not isinstance(filter_cond.value, list):
                return False, f"{filter_cond.operator.value} operator requires a list"
            if not filter_cond.value:
                return False, f"{filter_cond.operator.value} list cannot be empty"
        
        elif filter_cond.operator == FilterOperator.BETWEEN:
            if not isinstance(filter_cond.value, list) or len(filter_cond.value) != 2:
                return False, "between operator requires a list with exactly 2 values"
        
        elif filter_cond.operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            if filter_cond.value is not None:
                return False, f"{filter_cond.operator.value} operator doesn't accept a value"
        
        elif filter_cond.operator in [FilterOperator.LIKE, FilterOperator.STARTSWITH, FilterOperator.ENDSWITH]:
            if not isinstance(filter_cond.value, str):
                return False, f"{filter_cond.operator.value} operator requires a string value"
        
        return True, None


# Example usage and tests
def test_search_filter():
    """Test search and filtering functionality"""
    
    # Example 1: Using the builder
    print("Example 1: Using SearchFilterBuilder")
    builder = SearchFilterBuilder()
    criteria = (builder
                .add_eq("status", "active")
                .add_gt("age", 18)
                .add_like("name", "John")
                .set_sort("created_at", SortOrder.DESC)
                .set_search("developer", ["title", "description"])
                .set_pagination(1, 10)
                .build())
    
    print("Search Criteria:")
    print(json.dumps(criteria.to_dict(), indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Example 2: Query string parsing
    print("Example 2: Query String Parsing")
    query = "status:active age__gt:30 name:John sort:created_at desc search:developer"
    criteria = QueryParser.parse_query(query)
    print(f"Query: {query}")
    print(f"Parsed: {json.dumps(criteria.to_dict(), indent=2)}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 3: Advanced builder
    print("Example 3: Advanced Search Builder")
    advanced = (AdvancedSearchBuilder()
                .where_between("price", 10, 100)
                .where_eq("category", "electronics")
                .search_text("phone", ["name", "description"])
                .sort_by("rating", SortOrder.DESC)
                .page(1, 20)
                .facet("category", "brand")
                .aggregate("price", "avg", "avg_price")
                .aggregate("rating", "min", "min_rating")
                .build())
    
    print("Advanced criteria:")
    print(json.dumps(advanced.to_dict(), indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Building query parameters
    print("Example 4: Building Query Parameters")
    handler = SearchFilterHandler()
    params = handler.build_query_params(criteria)
    print("Query parameters:")
    print(json.dumps(params, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Example 5: Filter validation
    print("Example 5: Filter Validation")
    valid_filter = FilterCondition("age", FilterOperator.GT, 18)
    is_valid, error = FilterValidator.validate_filter(valid_filter)
    print(f"Valid filter: {is_valid}, Error: {error}")
    
    invalid_filter = FilterCondition("age", FilterOperator.IN, "not a list")
    is_valid, error = FilterValidator.validate_filter(invalid_filter)
    print(f"Invalid filter: {is_valid}, Error: {error}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 6: Real API example (commented out)
    print("Example 6: Real API Usage (commented)")
    # client = SearchableAPIClient("https://jsonplaceholder.typicode.com")
    # results = client.search("posts", "userId:1")
    # print(f"Found {results.total} posts")
    # print(f"Page {results.page} of {results.total_pages}")
    # print(f"First post: {results.data[0] if results.data else 'None'}")


def test_with_mock_api():
    """Test with mock API"""
    
    class MockAPI:
        """Mock API for testing search and filter"""
        
        def __init__(self):
            self.data = []
            # Generate mock data
            names = ["John Doe", "Jane Smith", "Bob Johnson", "Alice Williams", 
                    "Charlie Brown", "Diana Prince", "Edward Norton", "Fiona Apple"]
            statuses = ["active", "inactive", "pending", "active", "active", "inactive", "pending", "active"]
            ages = [25, 30, 35, 28, 42, 31, 29, 38]
            cities = ["NYC", "LA", "Chicago", "Miami", "Boston", "Seattle", "Austin", "Denver"]
            
            for i in range(50):
                idx = i % len(names)
                self.data.append({
                    "id": i + 1,
                    "name": names[idx] + (f" {i+1}" if i >= len(names) else ""),
                    "status": statuses[idx],
                    "age": ages[idx] + (i // len(ages)),
                    "city": cities[idx],
                    "created_at": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
                })
        
        def search(self, params):
            """Mock search endpoint"""
            # Start with all data
            results = self.data.copy()
            
            # Apply filters
            for key, value in params.items():
                if key == 'q':
                    # Text search
                    results = [item for item in results if value.lower() in item['name'].lower()]
                elif key == 'status':
                    results = [item for item in results if item['status'] == value]
                elif key == 'age__gt':
                    results = [item for item in results if item['age'] > int(value)]
                elif key == 'age__lt':
                    results = [item for item in results if item['age'] < int(value)]
                elif key == 'city':
                    results = [item for item in results if item['city'] == value]
            
            # Sorting
            if 'sort' in params:
                sort_field, sort_order = params['sort'].split(':')
                reverse = sort_order == 'desc'
                results.sort(key=lambda x: x.get(sort_field, ''), reverse=reverse)
            
            # Pagination
            page = int(params.get('page', 1))
            page_size = int(params.get('size', 10))
            start = (page - 1) * page_size
            end = start + page_size
            total = len(results)
            paginated = results[start:end]
            
            return {
                "data": paginated,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
    
    print("Testing with Mock API:")
    mock_api = MockAPI()
    
    # Create client with mock
    client = SearchableAPIClient("http://mock.api")
    # Override session get
    original_get = client.session.get
    
    def mock_get(url, **kwargs):
        class MockResponse:
            def __init__(self, data, status=200):
                self._data = data
                self.status_code = status
                self.text = json.dumps(data)
                self.headers = {}
            
            def json(self):
                return self._data
            
            def raise_for_status(self):
                pass
        
        params = kwargs.get('params', {})
        response_data = mock_api.search(params)
        return MockResponse(response_data)
    
    client.session.get = mock_get
    
    # Test search
    print("Search for active users in NYC:")
    results = client.search("users", "status:active city:NYC sort:name desc")
    print(f"Found {results.total} active users in NYC")
    print(f"Page {results.page} of {results.total_pages}")
    print(f"Results: {[item['name'] for item in results.data]}")
    
    print("\nSearch for users over 30:")
    builder = SearchFilterBuilder()
    criteria = (builder
                .add_gt("age", 30)
                .set_sort("age")
                .set_pagination(1, 5)
                .build())
    results = client.search("users", criteria)
    print(f"Found {results.total} users over 30")
    print(f"Showing page {results.page}")
    for item in results.data:
        print(f"  - {item['name']} (Age: {item['age']})")
    
    print("\nGet all users:")
    all_users = client.search_all("users", "status:active", max_pages=2)
    print(f"Fetched {len(all_users)} active users")


if __name__ == "__main__":
    test_search_filter()
    print("\n" + "="*50 + "\n")
    test_with_mock_api()
