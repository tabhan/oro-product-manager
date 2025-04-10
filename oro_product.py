#!/usr/bin/env python3

"""
Oro Product Manager
A script to create or update products in OroCommerce using their REST API.
This script handles authentication, product creation, and updates through the Oro API.
"""

import argparse
import os
import requests
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

def load_env_file(env_file='.env'):
    """
    Load environment variables from .env file.
    
    Args:
        env_file (str): Path to the .env file
        
    Raises:
        SystemExit: If there's an error loading the .env file
    """
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
    except FileNotFoundError:
        print(f"Warning: {env_file} file not found. Using system environment variables.")
    except Exception as e:
        print(f"Error loading {env_file}: {e}")
        sys.exit(1)

@dataclass
class Product:
    """
    Data class representing a product in OroCommerce.
    
    Attributes:
        sku (str): Product SKU (Stock Keeping Unit)
        name (str): Product name
        unit (Optional[str]): Product unit code (default: "item")
        inventory_status (Optional[str]): Inventory status (default: "in_stock")
    """
    sku: str
    name: str
    unit: Optional[str] = "item"
    inventory_status: Optional[str] = "in_stock"

    def to_api_data(self) -> Dict[str, Any]:
        """
        Convert Product instance to API request data format.
        
        Returns:
            Dict[str, Any]: Formatted data ready for API request
        """
        data = {
            "data": {
                "type": "products",
                "attributes": {
                    "sku": self.sku,
                    "status": "enabled",
                    "productType": "simple",
                    "featured": True,
                    "newArrival": True
                },
                "relationships": {
                    "owner": {
                        "data": {
                            "type": "businessunits",
                            "id": "1"
                        }
                    },
                    "organization": {
                        "data": {
                            "type": "organizations",
                            "id": "1"
                        }
                    },
                    "names": {
                        "data": [
                            {
                                "type": "productnames",
                                "id": "names-1"
                            }
                        ]
                    },
                    "attributeFamily": {
                        "data": {
                            "type": "attributefamilies",
                            "id": "1"
                        }
                    },
                    "inventory_status": {
                        "data": {
                            "type": "prodinventorystatuses",
                            "id": self.inventory_status
                        }
                    }
                }
            },
            "included": [
                {
                    "type": "productnames",
                    "id": "names-1",
                    "attributes": {
                        "fallback": None,
                        "string": self.name
                    },
                    "relationships": {
                        "localization": {
                            "data": None
                        }
                    }
                }
            ]
        }

        if self.unit:
            unit_precision = {
                "type": "productunitprecisions",
                "id": "product-unit-precision-id-1",
                "attributes": {
                    "precision": 0,
                    "conversionRate": 1,
                    "sell": 1
                },
                "relationships": {
                    "unit": {
                        "data": {
                            "type": "productunits",
                            "id": self.unit
                        }
                    }
                }
            }
            data["data"]["relationships"]["primaryUnitPrecision"] = {
                "data": {
                    "type": "productunitprecisions",
                    "id": "product-unit-precision-id-1"
                }
            }
            data["data"]["relationships"]["unitPrecisions"] = {
                "data": [
                    {
                        "type": "productunitprecisions",
                        "id": "product-unit-precision-id-1"
                    }
                ]
            }
            data["included"].append(unit_precision)

        return data

class OroProductManager:
    """
    Manager class for handling OroCommerce product operations.
    
    This class handles authentication, product retrieval, creation, and updates
    through the OroCommerce REST API.
    """
    
    def __init__(self):
        """
        Initialize OroProductManager with environment variables.
        
        Raises:
            SystemExit: If required environment variables are missing
        """
        # Load environment variables from .env file
        load_env_file()
        
        # Read environment variables
        self.base_url = os.environ.get('ORO_BASE_URL')
        self.client_id = os.environ.get('ORO_CLIENT_ID')
        self.client_secret = os.environ.get('ORO_CLIENT_SECRET')
        self.admin_path = os.environ.get('ORO_ADMIN_PATH')
        self.token = None

        # Validate required environment variables
        if not all([self.base_url, self.client_id, self.client_secret, self.admin_path]):
            print("Error: Missing required environment variables. Please ensure ORO_BASE_URL, ORO_CLIENT_ID, ORO_CLIENT_SECRET, and ORO_ADMIN_PATH are set.")
            print("You can set these in the .env file or as system environment variables.")
            sys.exit(1)

    def get_access_token(self) -> str:
        """
        Get OAuth2 access token from OroCommerce.
        
        Returns:
            str: Access token for API authentication
            
        Raises:
            SystemExit: If token retrieval fails
        """
        if self.token:
            return self.token

        token_url = f"{self.base_url}/oauth2-token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            self.token = response.json()['access_token']
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"Error getting access token: {e}")
            print(f"Please check your Oro configuration in .env file:")
            print(f"ORO_BASE_URL: {self.base_url}")
            print(f"ORO_CLIENT_ID: {self.client_id}")
            print(f"ORO_CLIENT_SECRET: {self.client_secret}")
            sys.exit(1)

    def get_headers(self) -> Dict[str, str]:
        """
        Get headers with authentication token for API requests.
        
        Returns:
            Dict[str, str]: Headers including authorization token
        """
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }

    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """
        Get product by SKU if it exists.
        
        Args:
            sku (str): Product SKU to search for
            
        Returns:
            Optional[Dict[str, Any]]: Product data if found, None otherwise
        """
        product_url = f"{self.base_url}/{self.admin_path}/api/products"
        search_url = f"{product_url}?filter[sku]={sku}"
        
        try:
            response = requests.get(search_url, headers=self.get_headers())
            response.raise_for_status()
            response_data = response.json()
            if 'data' in response_data and response_data['data']:
                return response_data['data'][0]
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error getting product: {e}")
            return None

    def create_or_update_product(self, product: Product) -> Dict[str, Any]:
        """
        Create or update a product based on whether it exists.
        
        Args:
            product (Product): Product instance to create or update
            
        Returns:
            Dict[str, Any]: API response data
            
        Raises:
            SystemExit: If API request fails
        """
        existing_product = self.get_product_by_sku(product.sku)
        if existing_product:
            # Update existing product
            product_url = f"{self.base_url}/{self.admin_path}/api/products/{existing_product['id']}"
            method = "PATCH"
            data = product.to_api_data()
            data["data"]["id"] = existing_product["id"]
            
            # Remove unit precision data for updates
            if "unitPrecisions" in data["data"]["relationships"]:
                del data["data"]["relationships"]["unitPrecisions"]
            if "primaryUnitPrecision" in data["data"]["relationships"]:
                del data["data"]["relationships"]["primaryUnitPrecision"]
            data["included"] = [item for item in data["included"] if item["type"] != "productunitprecisions"]
        else:
            # Create new product
            product_url = f"{self.base_url}/{self.admin_path}/api/products"
            method = "POST"
            data = product.to_api_data()

        try:
            print(f"Sending request with data: {data}")
            response = requests.request(
                method,
                product_url,
                headers=self.get_headers(),
                json=data
            )
            if not response.ok:
                error_detail = response.json() if response.content else "No error details available"
                print(f"Server response: {error_detail}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error creating/updating product: {e}")
            sys.exit(1)

def main():
    """
    Main function to parse command line arguments and execute product operations.
    
    Command line arguments:
        --sku: Product SKU (required)
        --name: Product name (required)
        --unit: Product unit code (optional, default: item)
        --inventory-status: Inventory status (optional, default: in_stock)
    """
    parser = argparse.ArgumentParser(description='Create or update a product in Oro')
    parser.add_argument('--sku', required=True, help='Product SKU')
    parser.add_argument('--name', required=True, help='Product name')
    parser.add_argument('--unit', default='item', help='Product unit code (default: item)')
    parser.add_argument('--inventory-status', default='in_stock', help='Inventory status (default: in_stock)')

    args = parser.parse_args()

    try:
        # Create Product instance from command line arguments
        product = Product(
            sku=args.sku,
            name=args.name,
            unit=args.unit,
            inventory_status=args.inventory_status
        )

        # Initialize OroProductManager and create/update product
        manager = OroProductManager()
        result = manager.create_or_update_product(product)
        
        if 'data' in result and 'id' in result['data']:
            print("\nProduct Operation Successful!")
            print("=" * 50)
            print(f"Product ID: {result['data']['id']}")
            print(f"Product SKU: {result['data']['attributes']['sku']}")
            
            # Get the product name from the included data
            for included in result.get('included', []):
                if included['type'] == 'productnames':
                    print(f"Product Name: {included['attributes']['string']}")
                    break
            
            print("=" * 50)
        else:
            print("\nError: Unexpected response format from server")
            print("Response data:", result)
            sys.exit(1)
        
    except Exception as e:
        print("\nError occurred while processing the request:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            print("\nServer response:")
            print(e.response.text)
        sys.exit(1)

if __name__ == "__main__":
    main() 