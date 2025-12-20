from langchain_google_genai import goo
import json

with open(r'C:\AI\project\knowledge_data\knowledge_data.json', 'r') as file:
    emails = json.load(file)
# print(type(emails), len(emails))
