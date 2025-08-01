import requests

def log_sale_to_gumroad(api_token, product_id, quantity=1):
    url = "https://api.gumroad.com/v2/sales"
    payload = {
        "access_token": api_token,
        "product_id": product_id,
        "quantity": quantity
    }
    res = requests.post(url, data=payload)
    return res.status_code, res.json()