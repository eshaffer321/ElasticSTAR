from elastic_transport import ObjectApiResponse
from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch 
from openai import OpenAI
from dotenv import load_dotenv
import os
from elasticstar import get_chatgpt_response, get_docs_with_semantic_search

# Load environment variables
load_dotenv()
index_name = os.environ.get("ELASTIC_INDEX_NAME")
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
elastic_client = Elasticsearch(
    os.environ.get("ELASTIC_SEARCH_ENDPOINT"),
    api_key=os.environ.get("ELASTIC_SEARCH_API_KEY"),
)

# Initialize Flask app
app = Flask(__name__)

@app.route('/semantic', methods=['POST'])
def semantic_search():
    """Endpoint for semantic search and ChatGPT integration."""
    data = request.json
    index_id = data.get('index_id', index_name)
    query = data.get('query')

    if not query:
        return jsonify({"error": "Query is required"}), 400

    try:
        # Perform semantic search
        search_results = get_docs_with_semantic_search(query, index_id)
        
        # Generate ChatGPT response
        chatgpt_response = get_chatgpt_response(search_results, query)


        response = {
            "query": query,
            "elastic_hits": search_results.body,
            "chatgpt_response": chatgpt_response
        }
        print(response)


        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = os.environ.get("PORT", 5000)
    app.run(debug=True, port=port)