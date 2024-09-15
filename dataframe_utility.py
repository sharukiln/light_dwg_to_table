import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode


def editable_dataframe(df):
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

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        enable_enterprise_modules=False,
        height=300,  # Customize height if needed
        reload_data=True
    )
    return grid_response['data']