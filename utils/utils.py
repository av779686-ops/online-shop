import json

def read_json(file_path):
    with open(file_path, "r") as file:
        content = file.read()

        return json.loads(content)
    
def write_json(file_path, content):
    with open(file_path, "w") as f:
        json.dump(content, f)
        return content