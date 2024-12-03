"""ElasticSTAR.

Usage:
  elasticstar.py run-all <directory> <company_resource_folder> <output_file>
  elasticstar.py search <query>
  elasticstar.py inference <index_id> <inference_id>
  elasticstar.py semantic <index_id> <query>

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import os
from docopt import docopt
from elasticsearch import Elasticsearch, exceptions

from openai import OpenAI
from src.entry_processor import EntryProcessor
from src.file_data_loader import FileDataLoader
from src.prompt_builder import PromptBuilder
from src.indexer import Indexer
import tiktoken
from dotenv import load_dotenv
import json

load_dotenv()
index_name = os.environ.get("ELASTIC_INDEX_NAME")
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
elastic_client = Elasticsearch(
        os.environ.get("ELASTIC_SEARCH_ENDPOINT"),  # Elasticsearch endpoint
        api_key=os.environ.get("ELASTIC_SEARCH_API_KEY"),
    )


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-4o")
    num_tokens = len(encoding.encode(string))
    return num_tokens

def build_prompts(data_entries, resource_folder):
    prompt_list = []
    for entry in data_entries:
      prompts = PromptBuilder(resource_folder=resource_folder).build_prompt(entry)
      prompt_list.append(prompts)
    print(f"Built {len(prompt_list)} prompts.")
    return prompt_list

def process_for_indexing(prompt_list, entry_processor: EntryProcessor):
    if not os.path.exists(output_file):
        with open(output_file, 'w') as f:
            json.dump([], f)
    
    prompt_count = 1
    processed_count = 0
    for prompt in prompt_list:
        print(f'Processing prompt {prompt_count} of {len(prompt_list)}')
        processed_result = entry_processor.process_prompt(prompt)
        
        if processed_result:
            with open(output_file, 'r+') as f:
                try:
                    existing_results = json.load(f)
                except json.JSONDecodeError:
                    existing_results = []
                existing_results.append(processed_result)
                f.seek(0)
                json.dump(existing_results, f, indent=2)
                f.truncate()
                processed_count += 1
        prompt_count += 1
    print(f"Processed {processed_count}/{len(prompt_list)} entries.")

def run_all(directory: str, resource_folder: str, output_file: str):
    """Run the full ElasticSTAR pipeline."""
    print("Step 1: Parsing entries...")
    file_data_loader = FileDataLoader(input_directory=directory)
    entry_processor = EntryProcessor(openai_client)
    entries = file_data_loader.process_directory()

    print("Step 2: Building prompts...")
    prompt_list = build_prompts(entries, resource_folder)

    print("Step 3: Processing prompts with AI...")
    process_for_indexing(prompt_list, entry_processor)

    print("Step 4: Indexing to elastic")
    data_enteries = file_data_loader.parse_json_file(output_file)
    indexer = Indexer(elastic_client, index_name=index_name)
    indexer.index_data(data_enteries)
    print("Run-all completed successfully!")

def setup_semantic_search_inference(inference_id):
    inference_list = elastic_client.inference.get()
    existing_ids = [ep["inference_id"] for ep in inference_list["endpoints"]]
    if inference_id in existing_ids:
      print(f"Inference {inference_id} already exists. Skipping creation attempt")
      return
    
    print(f"Creating a new inference with {inference_id}")
    try:
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
    except exceptions.BadRequestError as e:
        if e.message == 'resource_already_exists_exception':
            # This really should not happen since we check above. Seems like a bug in the client?
            print(f"Failed to create Inference {inference_id} because it already exists?")

def create_index(index_name, inference_id):
    elastic_client.indices.create(
        index=index_name,
        mappings={
        "properties": {
            "title": {
                "type": "semantic_text",
                "inference_id": inference_id,
            },
            "description": {
                "type": "semantic_text",
                "inference_id": inference_id,
            },
            "reasoning": {
                "type": "semantic_text",
                "inference_id": inference_id,
            },
            "relevance_score": {
                "type": "float"
            },
            "category": {
                "type": "keyword"
            },
            "source": {
                "type": "keyword"
            },
            "estimate_confidence": {
                "type": "keyword"
            }
        }
    }
        )
if __name__ == '__main__':
    arguments = docopt(__doc__, version='ElasticSTAR 0.1')

    if arguments['run-all']:
        directory = arguments["<directory>"]
        resource_folder = arguments["<company_resource_folder>"]
        output_file = arguments["<output_file>"]

        run_all(directory, resource_folder, output_file)

    if arguments['search']:
        print("Running search against elastic.")
        results = elastic_client.search(index=index_name, q=arguments['<query>'])
        print(results)

    if arguments["inference"]:
      inference_id = arguments["<inference_id>"]
      index_id = arguments["<index_id>"]
      setup_semantic_search_inference(inference_id)
      create_index(index_id, inference_id)
      with open('output.json', 'r') as f:
          documents = json.load(f)
      Indexer(elastic_client=elastic_client, index_name=index_id).index_data(documents)

    if arguments['semantic']:
      index_id = arguments["<index_id>"]
      query = arguments["<query>"]
      resp = elastic_client.search(
          index=index_id,
          body={
              "_source": {
                "excludes": ["*.inference"]  # Exclude all 'inference' details
              },
              "query": {
                  "semantic": {
                      "field": "description",
                      "query": query 
                  }
              }
          }
      )

      

        



      