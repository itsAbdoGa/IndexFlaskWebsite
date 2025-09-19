import sys
import json
import re

socketio = None

def init_utils(sio):
    global socketio
    socketio = sio

def log_message(message):
    print(f"Logging: {message}", flush=True)

def log_message_with_store(message, store=None):
    """Enhanced log_message that includes store information"""
    from utils import socketio
    
    # Log to console/file as usual
    log_message(message)
    
    # Emit to frontend with store information
    socketio.emit('log_update', {
        'message': message,
        'store': store
    })

def get_size_kb(data):
    return round(sys.getsizeof(json.dumps(data)) / 1024, 2)


def transform_samsclub_data(data):
    stores = []

    # Regex for parsing the store info from keys and values
    store_pattern = re.compile(
        r"Store\s+#(?P<id>\d+)\s*-\s*(?P<city>.*?),\s*(?P<state>[A-Z]{2})"
    )
    address_pattern = re.compile(
        r"Address:\s*\[(?P<address>.*?),\s*(?P<zip>\d{5})\]\((?P<url>https?://[^\)]+)\)"
    )
    stock_pattern = re.compile(r"Stock:\s*(\d+)")

    for key, value in data.get("aditionalInformation", {}).items():
        match_store = store_pattern.search(key)
        match_address = address_pattern.search(value)
        match_stock = stock_pattern.search(value)

        if match_store and match_address:
            stores.append({
                "zip": match_address.group("zip"),
                "address": match_address.group("address"),
                "city": match_store.group("city"),
                "storePrice": data.get("price"),
                "id": match_store.group("id"),
                "state": match_store.group("state"),
                "storeStock": int(match_stock.group(1)) if match_stock else 0
            })

    transformed = {
        "samsclub": {
            "stores": stores,
            "itemDetails": {
                "imageUrl": data.get("imageUrl"),
                "msrp": data.get("price"),
                "name": data.get("itemName"),
                "url": data.get("itemUrl")
            }
        }
    }
    return transformed


def extract_number(url: str) -> str:
    # Split the URL by '/' and return the last non-empty segment
    segments = [seg for seg in url.split('/') if seg]
    if segments:
        return segments[-1]
    return None