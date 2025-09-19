
# Simple configuration for each store's search setup
SEARCH_CONFIGS = {
    'walmart': {
        'schema': 'walmart',
        'tables': {
            'items': 'items',
            'stores': 'stores', 
            'inventory': 'store_items'
        },
        'joins': [
            "walmart.store_items si JOIN walmart.stores s ON si.store_id = s.id",
            "JOIN walmart.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price': ('si.price', 'Price'),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'salesfloor': ('si.salesfloor', 'Sales Floor'),
            'backroom': ('si.backroom', 'Backroom'),
            'aisles': ('si.aisles', 'Aisle'),
            'msrp': ('i.msrp', 'MSRP'),
            'image_url': ('i.image_url', 'Image'),
            'product_id': ('i.productid', 'Product ID'),
            'store_id': ('s.id', 'Store ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.price' ,
             'si.salesfloor', 'si.backroom', 'si.aisles',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.price <= ump.max_price"
    },
    
    'samsclub': {
        'schema': 'samsclub',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "samsclub.store_items si JOIN samsclub.stores s ON si.store_id = s.id",
            "JOIN samsclub.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'homedepot': {
        'schema': 'homedepot',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "homedepot.store_items si JOIN homedepot.stores s ON si.store_id = s.id",
            "JOIN homedepot.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','Storestock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'lowes': {
        'schema': 'lowes',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "lowes.store_items si JOIN lowes.stores s ON si.store_id = s.id",
            "JOIN lowes.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'target': {
        'schema': 'target',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "target.store_items si JOIN target.stores s ON si.store_id = s.id",
            "JOIN target.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'gamestop': {
        'schema': 'gamestop',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "gamestop.store_items si JOIN gamestop.stores s ON si.store_id = s.id",
            "JOIN gamestop.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'costco': {
        'schema': 'costco',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "costco.store_items si JOIN costco.stores s ON si.store_id = s.id",
            "JOIN costco.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'sephora': {
        'schema': 'sephora',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "sephora.store_items si JOIN sephora.stores s ON si.store_id = s.id",
            "JOIN sephora.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'kohls': {
        'schema': 'kohls',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "kohls.store_items si JOIN kohls.stores s ON si.store_id = s.id",
            "JOIN kohls.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'dollargeneral': {
        'schema': 'dollargeneral',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "dollargeneral.store_items si JOIN dollargeneral.stores s ON si.store_id = s.id",
            "JOIN dollargeneral.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'bjs': {
        'schema': 'bjs',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "bjs.store_items si JOIN bjs.stores s ON si.store_id = s.id",
            "JOIN bjs.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'bestbuy': {
        'schema': 'bestbuy',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "bestbuy.store_items si JOIN bestbuy.stores s ON si.store_id = s.id",
            "JOIN bestbuy.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
    'ace': {
        'schema': 'ace',
        'tables': {
            'items': 'items',
            'stores': 'stores',
            'inventory': 'store_items'
        },
        'joins': [
            "ace.store_items si JOIN ace.stores s ON si.store_id = s.id",
            "JOIN ace.items i ON si.item_id = i.id"
        ],
        'fields': {
            'upc': ('i.upc', 'UPC'),
            'name': ('i.name', 'Product Name'),
            'price' : ('si.storeprice',"Store Price"),
            'city': ('s.city', 'City'),
            'state': ('s.state', 'State'),
            'zipcode': ('s.zipcode', 'ZIP Code'),
            'address': ('s.address', 'Address'),
            'store_id': ('s.id', 'Store ID'),
            'stock' : ('si.storestock','StoreStock'),
            'product_id' : ('i.productid','Product ID')
        },
        'select_fields': [
            's.address', 's.city', 's.state', 's.zipcode', 's.id as store_id',
            'i.name', 'i.upc','i.productid','si.storeprice','si.storestock',
            'ump.max_price', 'ump.description', 'ump.net', 'ump.department',
            
        ],
        'deal_join': "LEFT JOIN main.upc_max_prices ump ON i.upc = ump.upc",
        'deal_condition': "si.storeprice <= ump.max_price",

    },
}
