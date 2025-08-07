import datetime
import os
import json
from motor.motor_asyncio import AsyncIOMotorClient
from tracos_integration.mapping.translation import Translator
from setup import CustomerSystemWorkorder
from tracos_integration.helpers.validator import Validator

async def get_workorders():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "tractian")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DATABASE]
    collection = db[MONGO_COLLECTION]

    cursor = collection.find({
        "$or": [
            { "isSynced": False },
            { "isSynced": { "$exists": False } }
        ]
    })

    workorders = []
    async for item in cursor:
        workorders.append(item)

    return workorders

def process_workorder(tracosWorkorder):
    required_fields = ['number', 'status', 'createdAt']
    missing_fields = Validator.validate_required_fields(tracosWorkorder, required_fields)

    if(len(missing_fields) != 0):
        # LOG MISSING FIELDS
        print(f"Missing fields for order {tracosWorkorder.get('number')}: {missing_fields}")
        return
    
    customerWorkorder = Translator.tracOS_to_customer(tracosWorkorder)
    save_file_on_folder(customerWorkorder)
    save_workorder_on_database(customerWorkorder)

def build_file_name(customerWorkorder: CustomerSystemWorkorder) -> str:
    return f"{customerWorkorder.get('orderNo')}.json"  

def save_file_on_folder(customerWorkorder: CustomerSystemWorkorder):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))

    output_dir = os.path.join(project_root, "data", "outbound")
    output_path = os.path.join(output_dir, build_file_name(customerWorkorder))

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(customerWorkorder, file, ensure_ascii=True, indent=4)

def save_workorder_on_database(customerWorkorder: CustomerSystemWorkorder):
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "tractian")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DATABASE]
    collection = db[MONGO_COLLECTION]

    filter = { "number": customerWorkorder["orderNo"] }
    value = { "$set": 
        { "isSynced": True, "syncedAt": datetime.datetime.now() }
    }
    collection.update_one(filter, value, upsert=True)
