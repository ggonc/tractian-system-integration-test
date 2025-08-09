from bson import json_util
import datetime
import os
import json
from tracos_integration.mapping.translation import Translator
from setup import CustomerSystemWorkorder, TracOSWorkorder
from tracos_integration.helpers.validator import Validator
from tracos_integration.persistence.db import DbHandler
from loguru import logger

async def get_workorders():
    try:
        logger.info("Getting TRACOS unsynced workorders from database...")
        MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")

        async with DbHandler() as db:
            collection = db[MONGO_COLLECTION]
            cursor = collection.find({
                "$or": [
                    { "isSynced": False },
                    { "isSynced": { "$exists": False } }
                ]
            })

            workorders = [item async for item in cursor]
            logger.info("Found {workorders_count} TRACOS workorders: {workorders}", workorders_count=len(workorders), workorders=json_util.dumps(workorders, indent=2))
            return workorders
    except Exception as e:
        logger.error(f"Failed to fetch workorders from database: {e}")
        return []

async def process_workorder(tracosWorkorder: TracOSWorkorder):
    try:
        required_fields = ['number', 'status', 'createdAt']
        missing_fields = Validator.validate_required_fields(tracosWorkorder, required_fields)

        if(len(missing_fields) != 0):
            logger.error(f"Aborted processing for workorder {tracosWorkorder['number']}! \nThe following required fields are missing or have no value: {missing_fields}")
            return
        
        customerWorkorder = Translator.tracOS_to_customer(tracosWorkorder)
        save_file_on_folder(customerWorkorder)
        await update_workorder_sync_info_on_database(customerWorkorder)
    except Exception as e:
        logger.error(f"Error processing workorder {tracosWorkorder['number']}: \nException: {e}")

def build_file_name(customerWorkorder: CustomerSystemWorkorder) -> str:
    return f"{customerWorkorder.get('orderNo')}.json"  

def save_file_on_folder(customerWorkorder: CustomerSystemWorkorder):
    try:
        logger.info("Saving CUSTOMER workorder as a file... {workorder}", workorder=json_util.dumps(customerWorkorder, indent=2))
        
        output_dir = os.getenv("DATA_OUTBOUND_DIR", "data/outbound")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, build_file_name(customerWorkorder))

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(customerWorkorder, file, ensure_ascii=True, indent=4, default=str)
            logger.info(f"Saved workorder {customerWorkorder['orderNo']} as a file on outbound folder.")
    except Exception as e:
        logger.error(f"Failed to save workorder {customerWorkorder['orderNo']} as a file: \nException: {e}")

async def update_workorder_sync_info_on_database(customerWorkorder: CustomerSystemWorkorder):
    logger.info(f"Updating workorder {customerWorkorder['orderNo']} syncronization status on database... ")
    
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")

    async with DbHandler() as db:
        collection = db[MONGO_COLLECTION]

        filter = { "number": customerWorkorder["orderNo"] }
        value = { "$set": 
            { "isSynced": True, "syncedAt": datetime.datetime.now() }
        }
        await collection.update_one(filter, value, upsert=True)
        logger.info(f"Workorder {customerWorkorder['orderNo']} synced on database!")