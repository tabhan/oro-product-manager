#!/usr/bin/env python3

import argparse
import yaml
import requests
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class Product:
    sku: str
    name: str
    unit: Optional[str] = None
    inventory_status: Optional[str] = None

    def to_api_data(self) -> Dict[str, Any]:
        """Convert Product instance to API request data format."""
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
                            "id": self.inventory_status or "in_stock"
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
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.base_url = config['oro']['base_url']
            self.client_id = config['oro']['client_id']
            self.client_secret = config['oro']['client_secret']
            self.admin_path = config['oro']['admin_path']
            self.token = None

    def get_access_token(self) -> str:
        """Get OAuth2 access token from Oro."""
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
            sys.exit(1)

    def get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }

    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get product by SKU if it exists."""
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
        """Create or update a product based on whether it exists."""
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
    parser = argparse.ArgumentParser(description='Create or update a product in Oro')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--sku', required=True, help='Product SKU')
    parser.add_argument('--name', required=True, help='Product name')
    parser.add_argument('--unit', help='Product unit code')
    parser.add_argument('--inventory-status', help='Inventory status')

    args = parser.parse_args()

    try:
        # Create Product instance from command line arguments
        product = Product(
            sku=args.sku,
            name=args.name,
            unit=args.unit,
            inventory_status=args.inventory_status
        )

        manager = OroProductManager(args.config)
        result = manager.create_or_update_product(product)
        print("Product operation successful:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 