import json
import os
import glob
from tracos_integration.mapping.translation import Translator
from motor.motor_asyncio import AsyncIOMotorClient
from setup import CustomerSystemWorkorder, TracOSWorkorder
from tracos_integration.helpers.validator import Validator

def get_workorders():
    DATA_INBOUND_DIR = os.getenv("DATA_INBOUND_DIR", "data/inbound")
    files_paths = glob.glob(os.path.join(DATA_INBOUND_DIR, '*.json'))

    workorders = []
    for file_path in files_paths:
        workorder = get_workorder_from_files(file_path)
        workorders.append(workorder)
    
    return workorders

def get_workorder_from_files(filePath: str):
    with open(filePath, 'r', encoding="UTF-8") as f:
        return json.load(f)

def process_workorder(customerWorkorder: CustomerSystemWorkorder):
        required_fields = ['orderNo', 'creationDate']
        missing_fields = Validator.validate_required_fields(customerWorkorder, required_fields)

        if(len(missing_fields) != 0):
            # LOG MISSING FIELDS
            print(f"Missing fields for order {customerWorkorder.get('number')}: {missing_fields}")
            return

        tracosWorkorder = Translator.customer_to_tracOS(customerWorkorder)
        upsert_workorder_on_database(tracosWorkorder)

def upsert_workorder_on_database(tracosWorkorder: TracOSWorkorder):
    # Insert into DB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DATABASE = os.getenv("MONGO_DATABASE", "tractian")
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DATABASE]
    collection = db[MONGO_COLLECTION]

    # Blocks updates on deleted workorders
    filter = { "number": tracosWorkorder["number"], "deleted": False}
    
    value = { "$set": tracosWorkorder }
    collection.update_one(filter, value, upsert=True)

