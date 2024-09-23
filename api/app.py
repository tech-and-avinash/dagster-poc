from flask import Flask, request, jsonify
import requests
import os
import logging

app = Flask(__name__)

# Set up logging for the app
logging.basicConfig(level=logging.INFO)

# Set your Dagster instance details
DAGSTER_GRAPHQL_URL = os.getenv("DAGSTER_GRAPHQL_URL", "http://dagster_etl_webserver:3000/graphql")
# DAGSTER_GRAPHQL_URL = os.getenv("DAGSTER_GRAPHQL_URL", "http://localhost:3000/graphql")

@app.route('/webhook', methods=['POST'])
def handle_blob_created_event():
    try:
        events = request.json  # Azure Event Grid sends a list of events
        
        if not isinstance(events, list):
            app.logger.error("Invalid event format, expected a list")
            return jsonify({"error": "Invalid event format, expected a list"}), 400
        
        for event in events:
            event_data = event.get('data', {})
            
            # Handle webhook validation
            if 'validationCode' in event_data:
                app.logger.info("Handling Azure Event Grid validation event")
                validation_code = event_data['validationCode']
                return jsonify({"validationResponse": validation_code}), 200
            
            # Handle actual blob created event
            blob_url = event_data.get('url')
            if blob_url:
                app.logger.info(f"Blob created: {blob_url}")
                response = trigger_dagster_pipeline(blob_url)
                
                if response.status_code == 200:
                    app.logger.info(f"Pipeline triggered successfully for blob: {blob_url}")
                else:
                    app.logger.error(f"Failed to trigger pipeline for blob: {blob_url}, Status code: {response.status_code}, Response: {response.text}")
                    return jsonify({"error": "Failed to trigger pipeline", "details": response.text}), 500
            else:
                app.logger.error("Blob URL not found in event data")
                return jsonify({"error": "Blob URL not found in event data"}), 400
        
        return jsonify({"message": "Events processed"}), 200
    except Exception as e:
        app.logger.error(f"An error occurred while processing the event: {e}")
        return jsonify({"error": "Internal server error"}), 500

def trigger_dagster_pipeline(blob_url):
    """
    Sends a request to Dagster's GraphQL API to trigger the pipeline.
    """
    try:
        query = """
        mutation {
          launchPipelineExecution(
            input: {
              runConfigData: {
                solids: {
                  extract_task: {
                    config: {
                      blob_url: "%s"
                    }
                  }
                }
              }
              selector: {
                pipelineName: "etl_extract"
              }
            }
          ) {
            __typename
            ... on LaunchPipelineRunSuccess {
              run {
                runId
              }
            }
            ... on PythonError {
              message
            }
          }
        }
        """ % blob_url

        headers = {
            'Content-Type': 'application/json',
        }

        # Send the GraphQL mutation to Dagster to trigger the pipeline
        response = requests.post(DAGSTER_GRAPHQL_URL, json={"query": query}, headers=headers)
        response.raise_for_status()  # Raise an HTTPError if the response was unsuccessful
        return response
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Error while triggering Dagster pipeline: {e}")
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
