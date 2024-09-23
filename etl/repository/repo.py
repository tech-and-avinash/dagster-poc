from dagster import FilesystemIOManager, graph, op, repository, schedule, RunRequest, sensor, ConfigMapping
from dagster_docker import docker_executor
import os


# Define default config for the op
DEFAULT_BLOB_URL = "https://etlstoreqa.blob.core.windows.net/etl-container-qa/test4.txt"

# Operation to extract data from a blob URL
@op(config_schema={"blob_url": str})
def extract_from_blob(context):
    blob_url = context.op_config["blob_url"]
    context.log.info(f"Extracting data from blob: {blob_url}")
    # Add logic to download and extract the blob content here
    return blob_url


# Operation that processes the extracted data
@op
def process_data(context, extracted_data):
    context.log.info(f"Processing extracted data from blob: {extracted_data}")
    # Process the extracted data
    return extracted_data


# Graph definition for the ETL pipeline with a default configuration
@graph
def etl_graph():
    process_data(extract_from_blob())


# ConfigMapping to preload and provide default config if missing
def etl_default_config():
    return {
        "ops": {
            "extract_from_blob": {
                "config": {"blob_url": DEFAULT_BLOB_URL}
            }
        }
    }

# Job that runs the ETL pipeline with local execution and default config preloaded
etl_job = etl_graph.to_job(
    name="etl_job",
    config=etl_default_config()  # Preloading config for extract_from_blob
)

# Job that runs the ETL pipeline with Docker isolated execution and default config
etl_docker_job = etl_graph.to_job(
    name="etl_docker_job",
    executor_def=docker_executor,
    resource_defs={"io_manager": FilesystemIOManager(base_dir="/tmp/io_manager_storage")},
    config=etl_default_config()  # Preloading config for Docker job as well
)

# Schedule that runs the ETL pipeline every minute
@schedule(cron_schedule="* * * * *", job=etl_job, execution_timezone="US/Central")
def etl_schedule(_context):
    return etl_default_config()  # Ensure the default config is preloaded during scheduling


# Sensor that triggers the ETL pipeline when a blob is created
@sensor(job=etl_docker_job)
def blob_created_sensor(context):
    blob_url = os.getenv("NEW_BLOB_URL", DEFAULT_BLOB_URL)  # Default if env var is missing
    
    if blob_url:
        context.log.info(f"New blob detected: {blob_url}")
        run_config = {
            "ops": {
                "extract_from_blob": {
                    "config": {"blob_url": blob_url}
                }
            }
        }
        return RunRequest(run_key=blob_url, run_config=run_config)
    
    return None


# Repository definition
@repository
def etl_repository():
    return [etl_job, etl_docker_job, etl_schedule, blob_created_sensor]
