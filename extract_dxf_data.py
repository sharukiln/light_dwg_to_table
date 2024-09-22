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

def recalculate_df(cost_file, edited_df):
    # Copy the edited DataFrame to avoid modifying it in place
    df = edited_df.copy()

    # Drop the existing Totals and Fixture_Costs rows before recalculating
    df = df[df["Room"].isin(["Totals", "Fixture_Costs"]) == False]

    # Recalculate totals for each column except "Room"
    numeric_columns = [col for col in df.columns if col != "Room"]
    
    # Make sure to filter out any non-numeric columns for safety
    df[numeric_columns] = df[numeric_columns].apply(pandas.to_numeric, errors='coerce')
    
    totals = df.loc[df["Room"] != "Unit_Costs", numeric_columns].sum().to_frame().T
    totals["Room"] = "Totals"

    # Append recalculated totals back to the DataFrame
    df = pandas.concat([df, totals], ignore_index=True)

    # Extract unit costs for recalculating fixture costs
    unit_costs = df.loc[df["Room"] == "Unit_Costs", numeric_columns].values
    totals = df.loc[(df["Room"] == "Totals"), numeric_columns].values

    # If unit costs or totals are missing, return the DataFrame as is
    if unit_costs.size == 0 or totals.size == 0:
        streamlit.warning("Unit costs or totals are missing. No recalculations made.")
        return df

    # Recalculate fixture costs based on new totals and unit costs
    fixtures = pandas.DataFrame(totals * unit_costs)

    # Ensure the number of columns in 'fixtures' matches the original numeric_columns
    if fixtures.shape[1] == len(numeric_columns):
        fixtures.columns = numeric_columns
    else:
        # Handle mismatch in column count (if necessary)
        streamlit.error("Column mismatch during fixture calculation.")
        return df

    fixtures["Room"] = "Fixture_Costs"
    
    # Reorder columns to ensure "Room" is the first column
    fixtures = fixtures[["Room"] + numeric_columns]

    # Append the recalculated fixture costs to the DataFrame
    df = pandas.concat([df, fixtures], ignore_index=True)

    return df


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
    totals = df[df["Room"]!="Unit_Costs"].sum().reset_index().T
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
    # df.fillna('', inplace=True)
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
    dxf_file = file_upload()  # Function to upload DXF file
    cost_file = cost_file_upload()  # Function to upload cost file

    # Process the uploaded files and calculate the cost by group
    cost_by_group = get_count_by_group(dxf_file)
    display_table = make_table(cost_file, cost_by_group)

    # Show the table in a non-editable mode initially
    # streamlit.dataframe(display_table.fillna(""))

    # Expander for editing the DataFrame
    with streamlit.expander("Click to edit and view full DataFrame"):
        # Create an editable version of the DataFrame using `st.experimental_data_editor` (streamlit feature)
        edited_df = editable_dataframe(display_table)

        # Show the edited DataFrame
        # streamlit.write("### Edited DataFrame")
        # streamlit.dataframe(edited_df)

        # Recalculate based on the edited DataFrame
        if streamlit.button("Recalculate Table"):
            # Pass the edited_df back to the make_table function to recalculate
            recalculated_table = recalculate_df(cost_file, edited_df)
            streamlit.write("### Recalculated Table")
            streamlit.dataframe(recalculated_table.fillna(""))
