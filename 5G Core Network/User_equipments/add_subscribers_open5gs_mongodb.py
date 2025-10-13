from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB connection details
mongo_host = "10.105.255.235"
mongo_port = 27017
mongo_db = "open5gs"
mongo_collection = "subscribers"

# Subscriber data to be inserted




def new_subscriber(nbr_sub):
    subscriber = {
        #"_id": ObjectId("667c2133aedf377d8df93db8"),
        "ambr": {
            "downlink": {"value": 1, "unit": 3},
            "uplink": {"value": 1, "unit": 3}
        },
        "schema_version": 1,
        "msisdn": [],
        "imeisv": [],
        "mme_host": [],
        "mme_realm": [],
        "purge_flag": [],
        "access_restriction_data": 32,
        "subscriber_status": 0,
        "operator_determined_barring": 0,
        "network_access_mode": 0,
        "subscribed_rau_tau_timer": 12,
        "imsi": "9997"+"0"*(11-len(str(nbr_sub)))+str(nbr_sub+1),
        "security": {
            "k": "465B5CE8 B199B49F AA5F0A2E E238A6BC",
            "amf": "8000",
            "op": None,
            "opc": "E8ED289D EBA952E4 283B54E8 8E6183CA"
        },
        "slice": [
            {
                "_id": ObjectId("667c2133aedf37ba59f93db9"),
                "sst": 1,
                "default_indicator": True,
                "session": [
                    {
                        "qos": {
                            "arp": {
                                "priority_level": 8,
                                "pre_emption_capability": 1,
                                "pre_emption_vulnerability": 1
                            },
                            "index": 9
                        },
                        "ambr": {
                            "downlink": {"value": 1, "unit": 3},
                            "uplink": {"value": 1, "unit": 3}
                        },
                        "_id": ObjectId("667c2133aedf37394af93dba"),
                        "name": "internet",
                        "type": 3,
                        "pcc_rule": []
                    }
                ]
            }
        ],
        "__v": 0
    }
    return subscriber


try:
  # Connect to MongoDB
    client = MongoClient(mongo_host, mongo_port)
  # Access the Open5GS database
    db = client[mongo_db]
  # Access the subscribers collection
    collection = db[mongo_collection]
  # Insert the subscriber document
    nbr_sub=1
    total_sub=500
    while nbr_sub < total_sub:
    # Add the subscriber
        subscriber=new_subscriber(nbr_sub)
        result = collection.insert_one(subscriber)
        print(f"Subscriber added with _id: {result.inserted_id}")
        nbr_sub +=1 
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    client.close()



