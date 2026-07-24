import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("agentic_testing.database")

# In-memory storage fallback if MongoDB URI is not set or fails to connect
_in_memory_history: List[Dict[str, Any]] = []

def get_motor_client():
    if not settings.MONGODB_URI:
        return None
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=3000)
        return client
    except Exception as e:
        logger.warning(f"Failed to initialize Motor MongoDB client: {e}")
        return None

def save_local_output_files(document: Dict[str, Any], doc_id: str) -> Dict[str, str]:
    """
    Saves raw JSON output and Markdown report into app/output/raw_json/ and app/output/reports/
    """
    base_dir = os.path.dirname(os.path.dirname(__file__)) # d:\Brankas Semester 6\DIV-TI-III-23-27-714230012_Muflihafif\app
    raw_json_dir = os.path.join(base_dir, "output", "raw_json")
    reports_dir = os.path.join(base_dir, "output", "reports")

    os.makedirs(raw_json_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"test_run_{timestamp_str}_{doc_id[:8]}.json"
    md_filename = f"test_report_{timestamp_str}_{doc_id[:8]}.md"

    json_path = os.path.join(raw_json_dir, json_filename)
    md_path = os.path.join(reports_dir, md_filename)

    # Make a JSON serializable copy of document (convert ObjectId to str)
    doc_copy = dict(document)
    if "_id" in doc_copy:
        doc_copy["id"] = str(doc_copy["_id"])
        del doc_copy["_id"]

    # Save raw JSON file
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(doc_copy, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Failed to write raw JSON output file: {e}")

    # Save Markdown report file
    try:
        report_md = document.get("llm_evaluation", {}).get("report_md", "# Report")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_md)
    except Exception as e:
        logger.error(f"Failed to write Markdown report file: {e}")

    return {
        "json_filepath": f"app/output/raw_json/{json_filename}",
        "md_filepath": f"app/output/reports/{md_filename}"
    }

async def save_meal_plan(document: Dict[str, Any]) -> str:
    import uuid
    doc_id = str(uuid.uuid4())[:8]

    client = get_motor_client()
    if client:
        try:
            db = client[settings.DB_NAME]
            collection = db[settings.COLLECTION_NAME]
            result = await collection.insert_one(document)
            doc_id = str(result.inserted_id)
        except Exception as e:
            logger.error(f"MongoDB save failed: {e}. Falling back to in-memory store.")

    # Save to local file system in app/output/
    local_files = save_local_output_files(document, doc_id)
    document["local_files"] = local_files

    if not client:
        doc_copy = dict(document)
        doc_copy["_id"] = doc_id
        _in_memory_history.insert(0, doc_copy)

    return doc_id

async def get_meal_history(limit: int = 10) -> List[Dict[str, Any]]:
    client = get_motor_client()
    if client:
        try:
            db = client[settings.DB_NAME]
            collection = db[settings.COLLECTION_NAME]
            cursor = collection.find().sort("_id", -1).limit(limit)
            items = []
            async for doc in cursor:
                doc["id"] = str(doc.get("_id"))
                if "_id" in doc:
                    del doc["_id"]
                items.append(doc)
            return items
        except Exception as e:
            logger.error(f"MongoDB fetch failed: {e}. Returning in-memory history.")

    # Return in-memory fallback
    result = []
    for item in _in_memory_history[:limit]:
        item_copy = dict(item)
        item_copy["id"] = str(item_copy.get("_id", "mem_id"))
        if "_id" in item_copy:
            del item_copy["_id"]
        result.append(item_copy)
    return result
