"""Streamlit UI for the SuperKart sales forecasting API (single and batch predictions)."""
import os

import pandas as pd
import requests
import streamlit as st

# Inside the Docker network the backend is reachable by its container name
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:7860").rstrip("/")
REQUEST_TIMEOUT_SECONDS = 30

st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="centered")
st.title("🛒 SuperKart Sales Forecast")
st.write("Forecast the total sales revenue of a product in a store, one at a time or for a whole CSV file.")


def call_api(endpoint, **request_kwargs):
    """POST to the backend and return the JSON body, or show a readable error and return None."""
    try:
        response = requests.post(f"{BACKEND_URL}{endpoint}", timeout=REQUEST_TIMEOUT_SECONDS, **request_kwargs)
    except requests.exceptions.RequestException as error:
        st.error(f"Could not reach the prediction service at {BACKEND_URL}: {error}")
        return None
    if response.status_code != 200:
        try:
            message = response.json().get("error", response.text)
        except ValueError:
            message = response.text
        st.error(f"Prediction failed (HTTP {response.status_code}): {message}")
        return None
    return response.json()


single_tab, batch_tab = st.tabs(["Single Prediction", "Batch Prediction"])

with single_tab:
    st.subheader("Product details")
    col1, col2 = st.columns(2)
    product_weight = col1.number_input("Product weight", min_value=0.0, max_value=50.0, value=12.66, step=0.1)
    product_mrp = col2.number_input("Product MRP", min_value=1.0, max_value=500.0, value=117.08, step=1.0)
    product_allocated_area = col1.number_input(
        "Allocated display area (ratio)", min_value=0.0, max_value=1.0, value=0.027, step=0.001, format="%.3f"
    )
    product_sugar_content = col2.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
    product_id_char = col1.selectbox(
        "Product family", ["FD", "DR", "NC"], help="FD = food, DR = drinks, NC = non-consumables"
    )
    product_type_category = col2.selectbox("Product category", ["Perishables", "Non Perishables"])

    st.subheader("Store details")
    col3, col4 = st.columns(2)
    store_type = col3.selectbox(
        "Store type", ["Supermarket Type2", "Supermarket Type1", "Departmental Store", "Food Mart"]
    )
    store_size = col4.selectbox("Store size", ["Medium", "High", "Small"])
    store_location_city_type = col3.selectbox("City tier", ["Tier 2", "Tier 1", "Tier 3"])
    store_age_years = col4.number_input("Store age (years)", min_value=0, max_value=100, value=16, step=1)

    if st.button("Predict sales", type="primary"):
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_location_city_type,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": store_age_years,
            "Product_Type_Category": product_type_category,
        }
        result = call_api("/v1/predict", json=payload)
        if result is not None:
            st.success("Prediction complete")
            st.metric("Forecast Product_Store_Sales_Total", f"{result['Predicted Product_Store_Sales_Total']:,.2f}")
            with st.expander("Request sent to the API"):
                st.json(payload)

with batch_tab:
    st.write(
        "Upload a CSV with the columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
        "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, "
        "Store_Age_Years, Product_Type_Category."
    )
    uploaded_file = st.file_uploader("Batch CSV file", type=["csv"])
    if uploaded_file is not None:
        batch_data = pd.read_csv(uploaded_file)
        st.write(f"Preview ({len(batch_data)} rows):")
        st.dataframe(batch_data.head())

        if st.button("Predict batch", type="primary"):
            result = call_api(
                "/v1/predictbatch", files={"file": ("batch.csv", uploaded_file.getvalue(), "text/csv")}
            )
            if result is not None:
                batch_data["Predicted_Sales"] = [result[str(index)] for index in batch_data.index]
                st.success(f"Predicted {len(batch_data)} rows")
                st.metric("Total forecast revenue", f"{batch_data['Predicted_Sales'].sum():,.2f}")
                # Show the prediction first so it is visible without scrolling the table sideways
                st.dataframe(batch_data[["Predicted_Sales", *batch_data.columns.drop("Predicted_Sales")]])
                st.download_button(
                    "Download predictions as CSV",
                    data=batch_data.to_csv(index=False).encode("utf-8"),
                    file_name="superkart_predictions.csv",
                    mime="text/csv",
                )
