import ezdxf
import pandas
import streamlit
from io import BytesIO
import tempfile


def file_upload():
    uploaded_file = streamlit.file_uploader("Choose a dxf file", type="dxf")
    # Create a temporary file
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            # Write the uploaded file's content to the temporary file
            tmp_file.write(uploaded_file.read())
            temp_file_path = tmp_file.name

        doc = ezdxf.readfile(temp_file_path)
        return doc
    else:
        streamlit.write("Please upload a file.")
        streamlit.stop()
    

def count_lights_in_group(dxf_file, group_name):
    
    light_count = {}
    group_table = dxf_file.groups
    group = group_table.get(group_name)

    if group is None:
        print(f"Group '{group_name}' not found.")
        return
    
    print(f"Extracting blocks from group '{group_name}':")
    
    # Loop through the entities in the group
    for entity in group:
        if entity.dxftype() == 'INSERT':  # Only extract blocks
            print(entity.dxf.name)
            entity_name = entity.dxf.name
            if entity_name.startswith("SYM_R"):
                if entity_name in light_count:
                    light_count[entity_name] = light_count[entity_name]+1
                else:
                    light_count[entity_name] = 1
    
    return light_count


def make_table(cost_by_group):
    print(cost_by_group)
    df = pandas.DataFrame(cost_by_group).T
    df.fillna('', inplace=True)
    return df


def get_cost_by_group(dxf_file):
    cost_by_group = {}
    with open("config/group_names.txt", 'r') as file:
        group_names = file.read().splitlines()
    
    for group in group_names:
        
        light_count = count_lights_in_group(dxf_file, group)
        print("checking for group....:", group, ":", light_count)
        cost_by_group[group] = light_count
    
    return cost_by_group

if __name__ == "__main__":
    dxf_file_path = r"file.dxf"
    dxf_file = file_upload()
    cost_by_group = get_cost_by_group(dxf_file)
    display_table = make_table(cost_by_group)
    streamlit.dataframe(display_table)
