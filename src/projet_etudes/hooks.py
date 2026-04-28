import logging

from kedro.framework.hooks import hook_impl
from shared.energy_service import save_energy_log

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EnergyHook:
    """Kedro hook that measures energy consumption per node using codecarbon."""

    def __init__(self):
        self._trackers: dict = {}
        self._current_pipeline: str = "default"

    @hook_impl
    def before_pipeline_run(self, run_params, pipeline, catalog) -> None:
        self._current_pipeline = run_params.get("pipeline_name") or "default"

    @hook_impl
    def before_node_run(self, node, catalog, inputs, is_async, run_id) -> None:
        try:
            from codecarbon import EmissionsTracker

            tracker = EmissionsTracker(
                save_to_file=False,
                save_to_api=False,
                log_level="error",
                measure_power_secs=1,
            )
            tracker.start()
            self._trackers[node.name] = tracker
        except Exception as e:
            logger.warning(f"[EnergyHook] Could not start tracker for {node.name}: {e}")

    @hook_impl
    def after_node_run(self, node, catalog, inputs, outputs, is_async, run_id) -> None:
        tracker = self._trackers.pop(node.name, None)
        if tracker is None:
            return
        try:
            tracker.stop()
            d = tracker.final_emissions_data
            save_energy_log(
                pipeline_name=self._current_pipeline,
                node_name=node.name,
                run_id=str(run_id),
                duration_s=d.duration,
                energy_kwh=d.energy_consumed,
                cpu_power_w=d.cpu_power or 0.0,
                gpu_power_w=d.gpu_power or 0.0,
                ram_power_w=d.ram_power or 0.0,
                co2_kg=d.emissions,
                cpu_energy_kwh=d.cpu_energy or 0.0,
                gpu_energy_kwh=d.gpu_energy or 0.0,
                ram_energy_kwh=d.ram_energy or 0.0,
            )
            logger.info(
                f"[EnergyHook] {node.name}: "
                f"{d.energy_consumed * 1000:.4f} Wh | "
                f"{d.emissions * 1e6:.2f} µg CO₂"
            )
        except Exception as e:
            logger.warning(f"[EnergyHook] Could not save energy data for {node.name}: {e}")


class SparkHooks:
    @hook_impl
    def after_context_created(self, context) -> None:
        """Initialises a SparkSession using the config defined in project's conf folder (if available)."""
        try:
            from pyspark import SparkConf
            from pyspark.sql import SparkSession

            # Look for the spark config (will raise KeyError if not present)
            parameters = context.config_loader.get("spark", None)
            if parameters is None:
                # No spark config found, skip Spark init
                logger.info(
                    "[SparkHooks] No spark.yaml config found, skipping SparkSession initialization."
                )
                return

            spark_conf = SparkConf().setAll(parameters.items())
            # Initialise the spark session
            spark_session_conf = (
                SparkSession.builder.appName(context.project_path.name)
                .enableHiveSupport()
                .config(conf=spark_conf)
            )
            _spark_session = spark_session_conf.getOrCreate()
            _spark_session.sparkContext.setLogLevel("WARN")
            logger.info("[SparkHooks] SparkSession initialized.")
        except Exception as e:
            logger.info(f"[SparkHooks] Error initializing SparkSession: {e}")
            return
