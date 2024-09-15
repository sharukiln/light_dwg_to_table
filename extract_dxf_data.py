import ezdxf
import pandas
import streamlit
from io import BytesIO
import tempfile
from json_utility import load_json
from dataframe_utility import editable_dataframe


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
    

def cost_file_upload():
    uploaded_file = streamlit.file_uploader("Choose a json file", type="json")
    # Create a temporary file
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dxf") as tmp_file:
            # Write the uploaded file's content to the temporary file
            tmp_file.write(uploaded_file.read())
            temp_file_path = tmp_file.name

        doc = load_json(temp_file_path)
        return doc
    else:
        streamlit.write("Please upload a file.")
        streamlit.stop()
    

def count_lights_in_group(dxf_file, group_name):
    
    light_count = {}
    group_table = dxf_file.groups

    group = group_table.get(group_name)

    if group is None:
        # print(f"Group '{group_name}' not found.")
        return
    
    # print(f"Extracting blocks from group '{group_name}':")
    
    # Loop through the entities in the group
    for entity in group:
        if entity.dxftype() == 'INSERT':  # Only extract blocks
            # print(entity.dxf.name)
            entity_name = entity.dxf.name
            if entity_name.startswith("SYM_Light"):
                if entity_name in light_count:
                    light_count[entity_name] = light_count[entity_name]+1
                else:
                    light_count[entity_name] = 1
    
    return light_count


def make_table(cost_file, cost_by_group):
    df = pandas.DataFrame(cost_by_group).T.reset_index().rename(columns={'index': 'Room'})
    unit_costs = cost_file
    unit_costs = pandas.DataFrame(unit_costs).T.reset_index().rename(columns={'index': 'Room'})
    unit_costs.columns = unit_costs.iloc[0]   # Make the first row the header
    unit_costs = unit_costs[1:].reset_index(drop=True)
    unit_costs.rename(columns={"entity_name": "Room"})
    unit_costs["Room"] = "Unit_Costs"
    
    common_columns = list(unit_costs.columns.intersection(df.columns))
    df = df.merge(unit_costs, how="outer", on=common_columns).reset_index(drop=True)
    
    df.columns = df.columns.str.replace("SYM_Light_", "", regex=False)
    df = df.drop(columns=["entity_name"])

    row_to_bring_to_top = df.iloc[1]  # Get the row to bring to the top
    remaining_df = df.drop(index=1)    # Drop the row from the original DataFrame

    # Concatenate the row and the remaining DataFrame
    df_reordered = pandas.concat([row_to_bring_to_top.to_frame().T, remaining_df], ignore_index=True)
    
    df = df_reordered    
    totals = df.sum().reset_index().T
    totals = totals.reset_index(drop=True)
    totals.columns = totals.iloc[0]
    totals = totals.drop(index=0)
    totals["Room"] = "Totals"
    df = pandas.concat([df, totals], ignore_index=True)

    totals = df.loc[df["Room"] == "Totals", [i for i in df.columns if i not in ["Room"]]].values
    unit_costs = df.loc[df["Room"] == "Unit_Costs", [i for i in df.columns if i not in ["Room"]]].values

    fixtures = pandas.DataFrame(totals * unit_costs)
    fixtures["Room"] = "Fixture_Costs"
    fixtures = fixtures[["Room"] + [col for col in fixtures.columns if col!="Room"]]
    fixtures.columns = df.columns
   
    df = pandas.concat([df, fixtures], ignore_index=True)
    df.fillna('', inplace=True)
    return df


def get_count_by_group(dxf_file):
    count_by_group = {}
   
    group_table = dxf_file.groups

    for group in group_table:
        if "*" not in group[0]:
            light_count = count_lights_in_group(dxf_file, group[0])
            # print("checking for group....:", group, ":", light_count)
            count_by_group[group[0]] = light_count
    
    return count_by_group

if __name__ == "__main__":
    dxf_file = file_upload()
    cost_file = cost_file_upload()
    cost_by_group = get_count_by_group(dxf_file)
    display_table = make_table(cost_file, cost_by_group)
    # df = editable_dataframe(display_table)
    streamlit.dataframe(display_table)
    # with streamlit.expander("Click to edit and view full DataFrame"):
    #     # Display editable dataframe in expander
    #     edited_df = editable_dataframe(display_table)
    #     streamlit.write("### Edited DataFrame")
    #     streamlit.dataframe(edited_df)
