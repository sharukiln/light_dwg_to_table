import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode


def editable_dataframe(df):
    # Create grid options from dataframe
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configure default column settings
    gb.configure_default_column(
        editable=True,
        cellEditor="text",
        cellEditorParams={"useFormatter": True}
    )
    
    gb.configure_pagination(paginationAutoPageSize=True)  # Pagination if needed
    gb.configure_side_bar()  # Sidebar with filters and settings
    gb.configure_default_column(editable=True)  # All columns editable
    grid_options = gb.build()

    # Render the editable grid
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=600,  # Customize height if needed
        width="100%",  
        reload_data=True
    )

    # Extract the edited data from the grid
    updated_df = pd.DataFrame(grid_response['data'])

    # Convert the relevant columns to numeric (int) after editing
    # Assuming all columns except "Room" should be numeric
    for col in updated_df.columns:
        if col != "Room":  # Replace "Room" with any column that should stay non-numeric
            updated_df[col] = pd.to_numeric(updated_df[col], errors='coerce').astype("float")
    
    return updated_df