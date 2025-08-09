# TracOS ↔ Client Integration Flow

## Introduction
This project implements an **asynchronous Python service** that simulates the integration between Tractian's CMMS (**TracOS**) and a customer's ERP system.

The integration has two flows:
- **Inbound**: Client → TracOS
- **Outbound**: TracOS → Client

The client's system is simulated by **JSON files** representing API responses.  
The TracOS system is simulated by a **MongoDB instance**.

---

## Architecture Overview
The project is split into clear, semi-independent modules:

- **services/customers**  
  Handles inbound flow:  
  Reads client workorders from JSON files, validates required fields, translates them into the TracOS format, and performs an **idempotent upsert** into MongoDB.
  
- **services/tracos**  
  Handles outbound flow:  
  Fetches unsynced TracOS workorders from MongoDB, translates them to the client format, writes them to outbound JSON files, and marks them as synced.
  
- **mapping/translation**  
  Translates and normalizes data between the client and TracOS formats, including mapping status fields.
  
- **persistence/db**  
  Async MongoDB connection handler using `motor` with context manager support.
  
- **helpers**  
  Utility functions, e.g., generating UTC ISO-8601 timestamps.

> **Note:** This version is tailored for a specific TracOS ↔ sample client scenario.  
---

## Features Implemented
- Reads from `DATA_INBOUND_DIR` and writes to `DATA_OUTBOUND_DIR` (both configurable via environment variables).
- **Inbound flow**:
  - Reads all JSON files from the inbound directory.
  - Validates essential fields.
  - Translates to TracOS format.
  - Upserts into MongoDB by `number` (idempotent).
- **Outbound flow**:
  - Selects all workorders not marked as `isSynced=true`.
  - Translates to client format.
  - Saves as JSON in the outbound directory.
  - Marks as synced in MongoDB with `syncedAt`.
- Configurable **via `.env` file**.
- Informative logging using `loguru`.
- **End-to-end automated test** using `pytest`.

---
## Project Structure
```
tractian_integrations_engineering_technical_test/
├── docker-compose.yml                # MongoDB container configuration
├── pyproject.toml                     # Poetry configuration
├── setup.py                           # Script to populate sample inbound/outbound data
├── data/
│   ├── inbound/                       # Client → TracOS JSON files (input)
│   └── outbound/                      # TracOS → Client JSON files (output)
├── src/
│   ├── main.py                        # Main entrypoint running inbound + outbound flows
│   └── tracos_integration/
│       ├── services/
│       │   ├── customers/
│       │   │   ├── __init__.py
│       │   │   └── customer.py        # Inbound flow: reads, validates, translates, upserts to MongoDB
│       │   └── tracos/
│       │       ├── __init__.py
│       │       └── tracos.py          # Outbound flow: fetches unsynced, translates, saves, updates sync status
│       ├── mapping/
│       │   ├── __init__.py
│       │   └── translation.py         # Data translation between client and TracOS formats
│       ├── models/
│       │   ├── __init__.py
│       │   ├── customers/
│       │   │   └── customer_workorder.py  # TypedDict for customer workorder format
│       │   └── tractian/
│       │       └── tracos_workorder.py    # TypedDict for TracOS workorder format
│       ├── persistence/
│       │   ├── __init__.py
│       │   └── db.py                   # Async MongoDB handler using motor
│       ├── helpers/
│       │   ├── __init__.py
│       │   └── datetime_utils.py       # Utility for generating UTC ISO-8601 timestamps
│       └── __init__.py
└── tests/
    ├── __init__.py
    └── test_e2e_integration.py         # End-to-end integration test (inbound → Mongo → outbound)
```

## Requirements
- Python 3.11+
- Docker and Docker Compose
- Poetry (for dependency management)

---

## Installation Steps
1. **Clone the repository**
   ```bash
   git clone https://github.com/ggonc/tractian-system-integration-test
   cd tractian_integrations_engineering_technical_test
   ```

2. **Install dependencies with Poetry**
   ```bash
   # Install Poetry if you don't have it
   curl -sSL https://install.python-poetry.org | python -
   
   # Install dependencies
   poetry install
   ```

3. **Start MongoDB using Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run the setup script to initialize sample data**
   ```bash
   poetry run python setup.py
   ```

5. **Configure environment variables**
   ```bash
   # Create a .env file or export directly in your shell
   echo "MONGO_URI=mongodb://localhost:27017/tractian" > .env
   echo "DATA_INBOUND_DIR=./data/inbound" >> .env
   echo "DATA_OUTBOUND_DIR=./data/outbound" >> .env
   ```

## Future Improvements
- **MongoDB retry logic:** Implement exponential backoff on connection and operations to handle temporary connectivity issues.
- **Inbound file idempotency:** Move processed inbound files to a processed/ folder or track them to avoid reprocessing.
- **Generic module design:** Refactor services to make them fully reusable for different clients with minimal code changes.

## Troubleshooting

- **MongoDB Connection Issues**: Ensure Docker is running and the MongoDB container is up with `docker ps`
- **Missing Dependencies**: Verify Poetry environment is activated or run `poetry install` again
- **Permission Issues**: Check file permissions for data directories