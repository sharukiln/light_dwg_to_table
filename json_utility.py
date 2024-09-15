import streamlit
import json
import tempfile

def load_json(file_path):
    """Load JSON content from a file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        streamlit.error(f"Error reading JSON file: {e}")
        return {}

def save_json(data):
    """Save JSON data to a temporary file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as tmp_file:
        json.dump(data, tmp_file, indent=4)
        tmp_file_path = tmp_file.name
    return tmp_file_path

def edit_json(data):
    """Create Streamlit UI to edit JSON data."""
    streamlit.write("Edit JSON data below:")

    edited_data = streamlit.json(data)

    return edited_data
