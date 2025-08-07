"""Entrypoint for the application."""
import sys
import os
import asyncio
from loguru import logger

# Add the project root to sys.path
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from tracos_integration.services.customers.customer import get_workorders as get_customer_workorders, process_workorder as process_customer_workorder
from tracos_integration.services.tracos.tracos import get_workorders as get_tracos_workorders, process_workorder as process_tracos_workorder

async def main():
    """INBOUND"""
    logger.info("Starting inbound integration...")
    customer_workorders = get_customer_workorders()
    for customer_workorder in customer_workorders:
        process_customer_workorder(customer_workorder)
    logger.info("Finished inbound integration")
    
    """OUTBOUND"""
    logger.info("Starting outbound integration...")
    tracos_workorders = await get_tracos_workorders()
    for tracos_workorder in tracos_workorders:
        process_tracos_workorder(tracos_workorder)
    logger.info("Finished outbound integration")

if __name__ == "__main__":
    asyncio.run(main())
