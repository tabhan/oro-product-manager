# Oro Product Manager

A Python command-line tool for managing products in OroCommerce/OroCRM through their REST API.

## Features

- Create new products in Oro
- Update existing products
- Support for required and optional product attributes
- OAuth2 authentication
- YAML configuration support

## Requirements

- Python 3.6+
- Required Python packages:
  - requests
  - pyyaml
  - dataclasses (Python 3.7+)

## Installation

1. Clone the repository:
```bash
git clone git@github.com:tabhan/oro-product-manager.git
cd oro-product-manager
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `config.yaml` file in the project root with the following structure:

```yaml
oro:
  base_url: "https://your-oro-instance.com"
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  admin_path: "admin"  # or your custom admin path
```

## Usage

The script can be run with the following command-line arguments:

### Required Arguments:
- `--sku`: Product SKU (Stock Keeping Unit)
- `--name`: Product name

### Optional Arguments:
- `--unit`: Product unit code
- `--inventory-status`: Inventory status (e.g., "in_stock", "out_of_stock")
- `--config`: Path to configuration file (default: config.yaml)

### Examples

Create a new product:
```bash
python oro_product.py --sku "PROD001" --name "Test Product" --unit "item" --inventory-status "in_stock"
```

Update an existing product:
```bash
python oro_product.py --sku "PROD001" --name "Updated Product Name"
```

## Testing

After creating or updating a product, you can verify the changes using curl:

```bash
curl -X GET "https://your-oro-instance.com/admin/api/products?filter[sku]=PROD001" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/vnd.api+json"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 