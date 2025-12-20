# import chromadb
import json
with open(r'C:\AI\project\knowledge_data\knowledge_data.json', 'r') as file:
    emails = json.load(file)
    with open(r'C:\AI\project\knowledge_data\knowledge_data.json', 'w') as outfile:
        json.dump(emails, outfile, indent=4)
print(len(emails))