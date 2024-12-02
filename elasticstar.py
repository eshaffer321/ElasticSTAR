"""ElasticSTAR.

Usage:
  elasticstar.py run-all <directory> <company_resource_folder> <output_file>
  elasticstar.py search <query>

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import os
from docopt import docopt
from elasticsearch import Elasticsearch

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