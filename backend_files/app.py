"""SuperKart sales forecasting REST API.

Endpoints
- GET  /                 health check
- POST /v1/predict       single prediction from a JSON body
- POST /v1/predictbatch  batch predictions from an uploaded CSV file (form field "file")
"""
import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

MODEL_PATH = "superkart_model.joblib"

# Raw features the serialized pipeline expects, in training order
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]
CATEGORICAL_FEATURES = [
    "Product_Sugar_Content",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Product_Type_Category",
]
FEATURES = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]

superkart_api = Flask("SuperKart Sales Forecasting API")

# Load the model once at start-up instead of on every request
model = joblib.load(MODEL_PATH)


class InvalidInputError(ValueError):
    """Raised when the request data cannot be turned into valid model features."""


def prepare_features(frame):
    """Validate the raw input and return a DataFrame with the expected columns and data types."""
    missing = [col for col in FEATURES if col not in frame.columns]
    if missing:
        raise InvalidInputError(f"Missing required feature(s): {', '.join(missing)}")

    features = frame[FEATURES].copy()
    for col in NUMERIC_FEATURES:
        features[col] = pd.to_numeric(features[col], errors="coerce")
    invalid_numeric = [col for col in NUMERIC_FEATURES if features[col].isna().any()]
    if invalid_numeric:
        raise InvalidInputError(f"Non-numeric or empty value(s) in: {', '.join(invalid_numeric)}")

    for col in CATEGORICAL_FEATURES:
        features[col] = features[col].astype(str).str.strip()
    return features


def predict_sales(features):
    """Predict sales and round to 2 decimals (currency)."""
    return np.round(model.predict(features), 2)


@superkart_api.get("/")
def home():
    """Health check used to confirm the API is up."""
    return jsonify({"message": "Welcome to the SuperKart Sales Forecasting API", "status": "ok"})


@superkart_api.post("/v1/predict")
def predict_single():
    """Predict sales for one product-store combination sent as a JSON object."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object with the feature values."}), 400
    try:
        features = prepare_features(pd.DataFrame([payload]))
    except InvalidInputError as error:
        return jsonify({"error": str(error)}), 400

    prediction = float(predict_sales(features)[0])
    return jsonify({"Predicted Product_Store_Sales_Total": prediction})


@superkart_api.post("/v1/predictbatch")
def predict_batch():
    """Predict sales for every row of an uploaded CSV file; returns {row index: prediction}."""
    uploaded_file = request.files.get("file")
    if uploaded_file is None:
        return jsonify({"error": "Upload a CSV file in the 'file' form field."}), 400
    try:
        batch = pd.read_csv(uploaded_file)
    except (pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeDecodeError) as error:
        return jsonify({"error": f"Could not read the CSV file: {error}"}), 400
    if batch.empty:
        return jsonify({"error": "The uploaded CSV file has no rows."}), 400
    try:
        features = prepare_features(batch)
    except InvalidInputError as error:
        return jsonify({"error": str(error)}), 400

    predictions = predict_sales(features)
    return jsonify({str(index): float(value) for index, value in zip(batch.index, predictions)})


if __name__ == "__main__":
    # Local development only; the container runs the app with gunicorn
    superkart_api.run(host="0.0.0.0", port=7860)
