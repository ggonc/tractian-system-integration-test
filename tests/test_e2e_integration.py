import os, json, asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure Python can find the src/ folder when running tests
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from tracos_integration.services.customers.customer import process_workorder as process_customer_workorder
from tracos_integration.services.tracos.tracos import get_workorders as get_tracos_workorders, process_workorder as process_tracos_workorder

# Environment variables for MongoDB connection
os.environ["MONGO_URI"] = "mongodb://localhost:27017/tractian"
os.environ["MONGO_DATABASE"] = "tractian"
os.environ["MONGO_COLLECTION"] = "workorders"

def test_e2e_inbound_to_outbound(tmp_path):
    """End-to-end test from inbound (client) to outbound (TracOS)."""
    async def run():
        # Create temporary inbound and outbound directories for the test
        inbound_dir = tmp_path / "inbound"
        outbound_dir = tmp_path / "outbound"
        inbound_dir.mkdir()
        outbound_dir.mkdir()

        # Point environment variables to the temporary directories
        os.environ["DATA_INBOUND_DIR"] = str(inbound_dir)
        os.environ["DATA_OUTBOUND_DIR"] = str(outbound_dir)

        # Clear the MongoDB collection before starting the test
        client = AsyncIOMotorClient(os.environ["MONGO_URI"])
        db = client[os.environ["MONGO_DATABASE"]]
        coll = db[os.environ["MONGO_COLLECTION"]]
        await coll.delete_many({})

        # Step 1: Create a mock customer workorder
        customer_wo = {
            "orderNo": "123",
            "summary": "Order number #123",
            "creationDate": "2025-08-01T12:00:00Z",
            "lastUpdateDate": "2025-08-01T12:30:00Z",
            "isActive": True,
            "isPending": False,
            "isDone": False,
            "isOnHold": False,
            "isCanceled": False,
            "isDeleted": False,
            "deletedDate": None
        }

        # Step 2: Process inbound (client → MongoDB as TracOS format)
        await process_customer_workorder(customer_wo)
        doc = await coll.find_one({"number": "123"})
        assert doc is not None
        assert doc.get("title") == "Order number #123"

        # Step 3: Process outbound (MongoDB → client format)
        tracos_wos = await get_tracos_workorders()
        assert any(w.get("number") == "123" for w in tracos_wos)
        for wo in tracos_wos:
            if wo.get("number") == "123":
                await process_tracos_workorder(wo)

        # Step 4: Validate that the outbound file was generated
        out_file = outbound_dir / "123.json"
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            out_payload = json.load(f)
        assert out_payload["orderNo"] == "123"
        assert out_payload["summary"] == "Order number #123"

        # Step 5: Validate sync flags in MongoDB
        synced = await coll.find_one({"number": "123"})
        assert synced.get("isSynced") is True
        assert isinstance(synced.get("syncedAt"), str)

        # Close the MongoDB connection
        client.close()

    # Run the async flow inside a synchronous test
    asyncio.run(run())
