"""Flow Agent Module

This module provides tools for interacting with Lyrebird's flow functionality,
including querying flow records and flow details.
"""

from typing import List, Dict, Any
import requests

class FlowTools:
    """Tools for interacting with Lyrebird flow functionality.
    
    This class provides methods to query flow records and get detailed flow information
    from a running Lyrebird instance.
    """
    
    def __init__(self, base_url: str = 'http://localhost:9090'):
        """Initialize FlowTools.
        
        Args:
            base_url: Base URL of the Lyrebird instance
        """
        self.base_url = base_url.rstrip('/')
    
    def get_flow_list(self) -> List[Dict[str, Any]]:
        """Get list of all flow records.
        
        Returns:
            List of flow records, each containing basic request/response information
        
        Raises:
            requests.RequestException: If the request fails
        """
        response = requests.get(f'{self.base_url}/api/flow')
        response.raise_for_status()
        return response.json()
    
    def get_flow_detail(self, flow_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific flow.
        
        Args:
            flow_id: ID of the flow to retrieve
            
        Returns:
            Detailed flow information including full request/response data
            
        Raises:
            requests.RequestException: If the request fails
        """
        response = requests.get(f'{self.base_url}/api/flow/{flow_id}')
        response.raise_for_status()
        return response.json()