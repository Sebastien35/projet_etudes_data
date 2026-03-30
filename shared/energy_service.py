import logging
from datetime import datetime, timezone

from shared.mongo import mongo_client

logger = logging.getLogger(__name__)

COLLECTION = "energy_logs"


def save_energy_log(
    pipeline_name: str,
    node_name: str,
    run_id: str,
    duration_s: float,
    energy_kwh: float,
    cpu_power_w: float,
    gpu_power_w: float,
    ram_power_w: float,
    co2_kg: float,
    cpu_energy_kwh: float,
    gpu_energy_kwh: float,
    ram_energy_kwh: float,
) -> None:
    # Let exceptions propagate so the caller (EnergyHook) can log them with context
    mongo = mongo_client()
    collection = mongo.use_collection(COLLECTION)
    collection.insert_one(
        {
            "pipeline_name": pipeline_name,
            "node_name": node_name,
            "run_id": run_id,
            "timestamp": datetime.now(timezone.utc),
            "duration_s": round(duration_s, 3),
            "energy_kwh": float(energy_kwh),
            "cpu_power_w": float(cpu_power_w),
            "gpu_power_w": float(gpu_power_w),
            "ram_power_w": float(ram_power_w),
            "co2_kg": float(co2_kg),
            "cpu_energy_kwh": float(cpu_energy_kwh),
            "gpu_energy_kwh": float(gpu_energy_kwh),
            "ram_energy_kwh": float(ram_energy_kwh),
        }
    )


def get_energy_logs() -> list[dict]:
    try:
        mongo = mongo_client()
        collection = mongo.use_collection(COLLECTION)
        return list(collection.find({}, {"_id": 0}).sort("timestamp", -1))
    except Exception as e:
        logger.error(f"[energy_service] Failed to fetch energy logs: {e}")
        return []
