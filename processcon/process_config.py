
PROCESS_CONFIGS = {
    'walmart': {
        'schema' : 'walmart',
        'API': 'http://5.75.246.251:9099/stock/store',
        'itemquery': """
        INSERT INTO walmart.items (name, upc, productid, msrp, image_url)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (upc) DO UPDATE
        SET name = EXCLUDED.name,
            msrp = EXCLUDED.msrp,
            image_url = EXCLUDED.image_url,
            productid = EXCLUDED.productid
            """,

            'storequery': """
                INSERT INTO walmart.stores (id, address, city, state, zipcode)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """,

            'siquery': """
                INSERT INTO walmart.store_items (store_id, item_id, price, salesfloor, backroom, aisles)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (store_id, item_id) DO UPDATE
                SET price = EXCLUDED.price,
                    salesfloor = EXCLUDED.salesfloor,
                    backroom = EXCLUDED.backroom,
                    aisles = EXCLUDED.aisles
            """
        
    },
    'samsclub': {
            'schema' : 'samsclub',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO samsclub.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO samsclub.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO samsclub.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'homedepot': {
            'schema' : 'homedepot',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO homedepot.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO homedepot.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO homedepot.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'lowes': {
            'schema' : 'lowes',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO lowes.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO lowes.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO lowes.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'target': {
            'schema' : 'target',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO target.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO target.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO target.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'gamestop': {
            'schema' : 'gamestop',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO gamestop.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO gamestop.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO gamestop.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'costco': {
            'schema' : 'costco',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO costco.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO costco.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO costco.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'sephora': {
            'schema' : 'sephora',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO sephora.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO sephora.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO sephora.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'kohls': {
            'schema' : 'kohls',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO kohls.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO kohls.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO kohls.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'dollargeneral': {
            'schema' : 'dollargeneral',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO dollargeneral.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO dollargeneral.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO dollargeneral.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'bjs': {
            'schema' : 'bjs',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO bjs.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO bjs.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO bjs.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'bestbuy': {
            'schema' : 'bestbuy',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO bestbuy.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO bestbuy.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO bestbuy.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
    'ace': {
            'schema' : 'ace',
            "API":"http://5.75.246.251:9099/stock/store",
            "itemquery": """
                    INSERT INTO ace.items (name, upc, productid, image_url)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (upc) DO UPDATE 
                    SET name = excluded.name,
                        productid = excluded.productid,
                        image_url = excluded.image_url
                    """,
    
            "storequery": """
                        INSERT INTO ace.stores (id, address, city, state, zipcode)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """,
    
            "siquery": """
                        INSERT INTO ace.store_items (store_id, item_id, storeprice, storestock)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (store_id, item_id) DO UPDATE 
                        SET storestock = excluded.storestock,
                            storeprice = excluded.storeprice
            """
    },
}