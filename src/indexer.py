from elasticsearch import Elasticsearch as ElasticClient, exceptions
from src.entry_processor import EntryProcessor
import json
import hashlib
class Indexer:
    def __init__(self, elastic_client: ElasticClient, index_name="professional"):
        self.client = elastic_client
        self.index_name = index_name
        pass

    def create_json_hash(self, dict):
        dict_str = json.dumps(dict, sort_keys=True)
        hashed = hashlib.sha256(dict_str.encode('utf-8')).hexdigest()
        return hashed

    def index_data(self, documents):
        self.create_index()
        print(f"Inserting {len(documents)} document(s) into elastic index {self.index_name}")

        for doc in documents:
            # TODO: Make this use the bulk upload instead
            # using the hash of the content as the ID. Should make UUID part of the generation or add ID during inital hashing
            doc_hash = self.create_json_hash(doc)
            try:
                self.client.index(
                    index=self.index_name,
                    id=doc_hash,
                    document=doc
                )
            except exceptions.BadRequestError as e:
                if e.message == 'resource_already_exists_exception':
                    print(f"Skipped {doc_hash} document as it is already indexed")
                else:
                    raise e

            print("Successfully inserted document")

    def create_index(self):
        try:
            self.client.indices.create(index=self.index_name)
        except exceptions.BadRequestError as e:
            if e.message == 'resource_already_exists_exception':
                print(f"Skipped creating index {self.index_name} document as it is already indexed")
            else:
                raise e
 
           
