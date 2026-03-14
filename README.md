Apex LLM
Apex LLM is a multi-model AI comparison platform that allows users to compare responses from multiple Large Language Models using a single prompt.

The system works similarly to LLM Arena but provides a custom interface and integrates multiple AI models using the OpenRouter API.

This project helps developers, students, and researchers analyze how different AI models respond to the same query.

Features
Compare responses from multiple LLM models
Single prompt input system
Side-by-side response display
API integration with OpenRouter
Simple and lightweight interface
Docker based deployment
Tech Stack
Backend

Python
LiteLLM
Frontend

HTML
CSS
JavaScript
Deployment

Docker
Docker Compose
API Provider

OpenRouter
Project Structure
LLM-APEX
│
├── apex
│   └── app.py
│
├── Dockerfile
├── docker-compose.yml
├── litellm-config.yml
├── requirement.txt
└── README.md
Installation
Clone the repository

git clone https://github.com/vashish09/llm-apex.git
Move into the project directory

cd llm-apex
Install dependencies

pip install -r requirement.txt
Add your OpenRouter API key in the configuration file.

Run the project

docker-compose up
How It Works
User enters a prompt.
The prompt is sent to multiple LLM models using OpenRouter API.
Each model processes the prompt.
The responses are displayed side-by-side for comparison.
Supported Models
The platform supports multiple models through OpenRouter such as:

GPT models
Claude models
LLaMA models
Mistral models
Future Improvements
Add more AI models
Response ranking system
Prompt history
UI improvements
Performance analytics
Author
Vashish Ubhare
BSc Computer Science Student

GitHub: https://github.com/vashish09

License
This project is created for educational and research purposes.

Screenshots
landing page


chat page


output page



