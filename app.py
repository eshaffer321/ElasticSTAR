from flask import Flask, request, jsonify, render_template
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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form.get("query")
        if not query:
            return render_template("index.html", results="No query provided.")
        
        try:
            # Perform semantic search
            search_results = get_docs_with_semantic_search(query, os.environ.get("ELASTIC_INDEX_NAME"))
            
            # Generate ChatGPT response
            chatgpt_response = get_chatgpt_response(search_results, query)
            
            return render_template("index.html", results=chatgpt_response)
        except Exception as e:
            return render_template("index.html", results=f"Error: {str(e)}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))