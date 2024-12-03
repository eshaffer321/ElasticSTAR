import uuid
import os
from elasticsearch import Elasticsearch, exceptions
from dotenv import load_dotenv
load_dotenv()

# this is quite odd. I use a UUID to create an inference and still gives me a 400 due to the inference already exists?
def create_inference():
    # Generate a unique UUID for the inference ID
    inference_id = f"inference-{uuid.uuid4()}"
    print(f"Generated Inference ID: {inference_id}")

    # Initialize the Elasticsearch client
    elastic_client = Elasticsearch(
        os.environ.get("ELASTIC_SEARCH_ENDPOINT"),  # Elasticsearch endpoint
        api_key=os.environ.get("ELASTIC_SEARCH_API_KEY"),
    )

    try:
        # Create the inference
        resp = elastic_client.inference.put(
            task_type="sparse_embedding",
            inference_id=inference_id,
            inference_config={
                "service": "elasticsearch",
                "service_settings": {
                    "adaptive_allocations": {
                        "enabled": True,
                        "min_number_of_allocations": 1,
                        "max_number_of_allocations": 10
                    },
                    "num_threads": 1,
                    "model_id": ".elser_model_2"
                }
            },
        )
        print("Inference created successfully!")
        print(resp)

    except exceptions.BadRequestError as e:
        if e.message == 'resource_already_exists_exception':
            print(f"Inference {inference_id} already exists!")
            print("This really should not be possible since this is using a UUID?")
        else:
            print(f"Failed to create inference: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_inference()