import json
import grequests
import requests
from core.database import get_db_connection
from utils import extract_number,log_message_with_store
from processcon.process_config import PROCESS_CONFIGS 
import time
import gevent


def store_upc_zip(upc, zip_code,store):
    """Store the UPC-ZIP combination in the database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        current_time = int(time.time())
        
        cursor.execute("""
            INSERT INTO main.olditem (upc, zip, timestamp,store)
            VALUES (%s, %s, %s,%s)
            ON CONFLICT (upc, zip) DO UPDATE
            SET timestamp = EXCLUDED.timestamp , store = EXCLUDED.store
        """, (upc, zip_code, current_time,store))
        
        conn.commit()



def process_entry(upc, zip_code,store):
    conf = PROCESS_CONFIGS[store]
    store_upc_zip(upc, zip_code,store)
        
        
    if len(zip_code) < 5:
        zip_code = "0"+zip_code
        
    """Process a single UPC-ZIP entry by sending a request and storing data"""


    if not upc or not zip_code:
        print("Skipping entry with missing UPC or Zipcode")
        
        


    payload = json.dumps({"storeName": store, "upc": upc, "zip": zip_code})
    headers = {'Content-Type': 'application/json'}


    try:
        # Using grequests for async requests
        rs = (grequests.post(conf["API"],timeout = 60, headers=headers, data=payload))
        response = grequests.map([rs], exception_handler=lambda req, e: None, size=1, gtimeout=60)[0]
        response_data = response.json()
    
    except (requests.exceptions.RequestException, json.JSONDecodeError, AttributeError) as e:
        log_message_with_store(f"Error processing {upc}: {str(e)}",store)
        return False

    if "stores" not in response_data or "itemDetails" not in response_data:
        log_message_with_store(f"Skipping {upc} due to missing data",store)
        log_message_with_store(f"Response: {response_data}",store)
        return False

    with get_db_connection() as conn:
        cursor = conn.cursor()
        item = response_data["itemDetails"]
        schema = conf['schema']
        productid = extract_number(item.get("url"))

        try:
            with gevent.Timeout(30, Exception("DB insert timeout")):
                if store == "walmart":
                    cursor.execute(
                        conf["itemquery"],
                        (item["name"], upc, productid, item.get("msrp"), item.get("imageUrl"))
                    )
                else:
                    cursor.execute(
                        conf["itemquery"],
                        (item["name"], upc, productid, item.get("imageUrl"))
                    )
        except Exception as e:
            log_message_with_store(f"DB error (item insert): {e}", store)
            return False

        try:
            with gevent.Timeout(30, Exception("DB commit timeout")):
                conn.commit()
        except Exception as e:
            log_message_with_store(f"DB error (commit after item insert): {e}", store)
            return False

        try:
            with gevent.Timeout(30, Exception("DB select timeout")):
                cursor.execute(f"SELECT id FROM {schema}.items WHERE upc = %s", (upc,))
                item_id = cursor.fetchone()[0]
                log_message_with_store("Done selecting item id",store)
        except Exception as e:
            log_message_with_store(f"DB error (fetch item_id): {e}", store)
            return False

        for location in response_data["stores"]:
            store_id = int(location["id"])
            try:
                with gevent.Timeout(30, Exception("DB store insert timeout")):
                    cursor.execute(
                        conf["storequery"],
                        (store_id, location["address"], location["city"], location["state"], location["zip"])
                    )
            except Exception as e:
                log_message_with_store(f"DB error (store insert): {e}", store)
                return False

            try:
                with gevent.Timeout(30, Exception("DB siquery timeout")):
                    if store == "walmart":
                        cursor.execute(
                            conf["siquery"],
                            (
                                store_id,
                                item_id,
                                location["price"],
                                location.get("salesFloor", 0),
                                location.get("backRoom", 0),
                                location.get("aisles", "None"),
                            )
                        )
                    else:
                        cursor.execute(
                            conf["siquery"],
                            (
                                store_id,
                                item_id,
                                location["storePrice"],
                                location["storeStock"],
                            )
                        )
            except Exception as e:
                log_message_with_store(f"DB error (siquery insert): {e}", store)
                return False

        try:
            with gevent.Timeout(30, Exception("DB final commit timeout")):
                conn.commit()
        except Exception as e:
            log_message_with_store(f"DB error (final commit): {e}", store)
            return False

        log_message_with_store(f"Processed: UPC {upc}, ZIP {zip_code}", store)
    return True