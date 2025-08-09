import json
import os
import glob
from tracos_integration.mapping.translation import Translator
from setup import CustomerSystemWorkorder, TracOSWorkorder
from tracos_integration.helpers.validator import Validator
from tracos_integration.persistence.db import DbHandler
from loguru import logger

def get_workorders():
    logger.info("Getting CUSTOMER workorders from inbound folder...")
    DATA_INBOUND_DIR = os.getenv("DATA_INBOUND_DIR", "data/inbound")
    files_paths = glob.glob(os.path.join(DATA_INBOUND_DIR, '*.json'))

    workorders = []
    for file_path in files_paths:
        workorder = get_workorder_from_files(file_path)
        if(workorder is None):
            # Skip corrupted files
            continue
        logger.info("Workorder found: {workorder}", workorder=json.dumps(workorder, indent=2))
        workorders.append(workorder)
    return workorders

def get_workorder_from_files(filePath: str):
    try:
        with open(filePath, 'r', encoding="UTF-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to read or parse file on {filePath}: \nException: {e}")
        return None

async def process_workorder(customerWorkorder: CustomerSystemWorkorder):
    try:
        required_fields = ['orderNo', 'creationDate']
        missing_fields = Validator.validate_required_fields(customerWorkorder, required_fields)

        if(len(missing_fields) != 0):
            logger.error(f"Aborted processing for workorder {customerWorkorder['orderNo']}! \nThe following required fields are missing or have no value: {missing_fields}")
            return

        tracosWorkorder = Translator.customer_to_tracOS(customerWorkorder)
        await upsert_workorder_on_database(tracosWorkorder)
    except Exception as e:
        logger.error(f"Error processing workorder {customerWorkorder['orderNo']}: \nException: {e}")

async def upsert_workorder_on_database(tracosWorkorder: TracOSWorkorder):
    logger.info("Upserting TRACOS workorder on database... {workorder} ", workorder=json.dumps(tracosWorkorder, indent=2))

    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "workorders")

    async with DbHandler() as db:
        collection = db[MONGO_COLLECTION]

        # Updates only non-deleted workorders
        filter = { "number": tracosWorkorder["number"], "deleted": False}
        value = { "$set": tracosWorkorder }
        
        await collection.update_one(filter, value, upsert=True)
        logger.info(f"Workorder {tracosWorkorder['number']} created/updated on database!")