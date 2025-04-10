# Oro Product Manager

A simple Python script to create or update products in OroCommerce.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Oro credentials:
```bash
ORO_BASE_URL=https://your-oro-instance.com
ORO_CLIENT_ID=your_client_id
ORO_CLIENT_SECRET=your_client_secret
ORO_ADMIN_PATH=admin
```

## Usage

Create or update a product:
```bash
python oro_product.py --sku "PRODUCT-SKU" --name "Product Name" [--unit "unit_code"] [--inventory-status "status"]
```

### Required Parameters
- `--sku`: Product SKU
- `--name`: Product name

### Optional Parameters
- `--unit`: Product unit code (default: "item")
- `--inventory-status`: Inventory status (default: "in_stock")

## Testing

Verify product creation/update:
```bash
curl -X GET "https://your-oro-instance.com/api/products/PRODUCT-SKU" \
-H "Authorization: Bearer $(curl -s https://your-oro-instance.com/oauth2-token \
-d 'client_id=your_client_id' \
-d 'client_secret=your_client_secret' \
-d 'grant_type=client_credentials' | jq -r '.access_token')"
```

## Security

- Keep your `.env` file secure
- Never commit sensitive credentials to version control 