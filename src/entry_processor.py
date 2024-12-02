import hashlib
import os
import json

class EntryProcessor:
    def __init__(self, openai_client, model="gpt-4o-mini", hash_output_file="hash.json"):
        self.openai_client = openai_client
        self.hash_output_file=hash_output_file
        self.model = model

    def ensure_json_file_exists(self):
        if not os.path.exists(self.hash_output_file):
            with open(self.hash_output_file, 'w') as f:
                json.dump([], f)

    def read_hash_file(self):
        self.ensure_json_file_exists()
        with open(self.hash_output_file, 'r') as f:
            return json.load(f)
        
    def update_hash_file(self, hash_data):
        with open(self.hash_output_file, 'w') as f:
            json.dump(hash_data, f)

    def process_prompt(self, prompt):
        prompt_hash = self.create_prompt_hash(prompt)
        hash_data = self.read_hash_file()

        if prompt_hash in hash_data:
            print(f"Skipping hash {prompt_hash} as it is already processed")
            return
        
        response = self.transform_with_ai(prompt)
        if response:
            hash_data.append(prompt_hash)
            self.update_hash_file(hash_data)
        return response
    
    def transform_with_ai(self, prompt):
        completion = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are helpful assistance that converts raw DATA to json schema. Leave out any backticks for formatting just leave raw json"},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            print(f"Invalid JSON in API response: {completion}")
            return None

    def create_prompt_hash(self, prompt: str):
        """
        Generates a SHA-256 hash for the given prompt.

        Args:
            prompt (str): The input string to be hashed.

        Returns:
            str: The hexadecimal representation of the SHA-256 hash of the input prompt.
        """
        hash_object = hashlib.sha256()
        hash_object.update(prompt.encode())
        hash_hex = hash_object.hexdigest()
        return hash_hex


