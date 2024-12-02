from pathlib import Path


class PromptBuilder:
    def __init__(self, resource_folder):
        self.resource_folder = resource_folder

    def get_company_info(self):
        """
        Retrieves company information by reading all files in the resource folder.
        Maps filenames to their contents for better labeling in the prompt.

        Returns:
            dict: A dictionary where keys are file labels and values are file contents.
        """
        path = Path(self.resource_folder)
        company_info = {}

        # Iterate over all files i
        for file in path.rglob("*"):
            if file.is_file(): 
                label = file.stem.replace("_", " ").title()
                try:
                    with open(file, 'r') as f:
                        company_info[label] = f.read()
                except Exception as e:
                    print(f"Error reading file {file}: {e}")

        return company_info
    
    def build_prompt_messages(self, entries):
        prompts = []
        company_content = self.get_company_info()
        for entry in entries:
            pass

    def get_user_prompt(self):
        pass

    def get_system_message(self):
        system_message = "You are a helpful assistant that is going to output only raw JSON with no formatting or backticks.\
                The format will comply with the example schema"
        return {"role": "system", "content": system_message}
    

    def build_prompt(self, entry):
        company_data = self.get_company_info()
        prompt = f"""
    You are an assistant transforming diverse work-related data into a structured format for Elasticsearch indexing. 
    Your goal is to normalize entries, enrich them with relevant insights, and prioritize alignment with company-provided information.

    Here is the input entry:
    {entry}

    Here is Company-Specific Information to guide your transformation:
    {company_data}

    Your task:
    1. Normalize the entry into a consistent JSON format with no formatting or backticks and the following fields:
    - `title`: A concise summary of the entry.
    - `description`: A detailed explanation of the entry.
    - `tags`: A list of concise, relevant keywords derived from:
    - Key technologies or tools explicitly mentioned in the entry (e.g., Terraform, Docker, Python, Java).
    - Company values (e.g., "Customer, 1st" or "Progress, SIMPLE Perfection").
    - Broader themes (e.g., "CI/CD Optimization" or "Resource Utilization").
        Avoid company-specific tool names unless context is critical to understanding the entry.
    - `reasoning`: Provide a detailed explanation of:
        - Why certain tags were chosen, especially for matching company values or key technologies.
        - Broader impact of the entry, including its contribution to company goals or mission (e.g., "This work enhances scalability, aligning with Elastic’s value of 'Speed, Scale, and Relevance.'").
        - Justify relevance scores based on alignment with company goals and the completeness of the data.

    - `relevance_score`: Assign a score from 0 to 1 based on:
        - How well the entry aligns with company values and technologies.
        - The completeness of the provided data (e.g., fewer details result in a lower score).

    - `category`: Suggest a category aligning with the job role or key themes of the entry (e.g., "CI/CD Optimization" or "Automation").

    - `source`: Specify the origin of the entry (e.g., "quarterly review" or "work item").

    2. Be mindful that some entries might have little information. For such entries:
    - Provide a lower relevance score.
    - Acknowledge the lack of sufficient data in the reasoning field.
    3. Estimate metrics if explicit data is unavailable:
    - Provide plausible estimates for metrics (e.g., "Test rerun latency reduction estimated at 50% due to parallel execution").
    - Justify estimates in terms of their basis (e.g., "Based on the transition to static VM provisioning").

    4. Avoid company-specific jargon:
    - Use the internal tool mapping to transform any company specific tools to generic terms. Look for mapping in company data 

    5. Include company value tags:
    - Explicitly link the work described to company values if applicable.

    Output your response in the following JSON format:
    {{
        "title": "Concise title here",
        "description": "Detailed description here",
        "tags": ["tag1", "tag2"], // This must include a tag for company value. Keep these concise and avoid company specific tool names and use the tool context above. Include tags such as "Parallel Execution", "CI/CD Optimization", or "Scalability" if relevant. Also don't include tags from the job posting if they are not in the entry.
        "reasoning": "Explanation of tag choices and alignment with company values. Include metrics and quantify the result if available",
        "relevance_score": 0.8, // This should be a factor of how details the input data was and how well it aligns with company value tag
        "category": "Optional category if applicable", // consider categories that more closely align with role description
        "source": "The origin of the entry (e.g., 'quarterly review', 'work item')"
        "metrics_needed": [] // List out what metrics are missing if any are needed.
        "metrics_estimate": "metrics_estimate": [
    {{
        "metric": "Test rerun latency reduction",
        "estimate": "50%",
        "basis": "Enhanced parallel execution and static provisioning"
    }},
    {{
        "metric": "VM provisioning delays",
        "estimate": "Several minutes",
        "basis": "Static VM provisioning enhancements"
    }}
] // Here is an example. include a list of estimated metrics that may have been accomplished if it can be infered. 
        "estimate_confidence": "High" // or "Moderate", "Low". What is the confidence level of the metrics estimate?
    }}
    """
        return prompt


            

    