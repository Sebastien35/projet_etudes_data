import logging

from kedro.framework.hooks import hook_impl
from pyspark import SparkConf
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SparkHooks:
    @hook_impl
    def after_context_created(self, context) -> None:
        """Initialises a SparkSession using the config defined in project's conf folder (if available)."""
        try:
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
