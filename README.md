# SuperKart Sales Forecasting – Deployment

Containerised deployment of the SuperKart sales forecasting model (tuned Random Forest pipeline, test R² ≈ 0.93).

```
backend_files/   Flask REST API (app.py, requirements.txt, Dockerfile, superkart_model.joblib)
frontend_files/  Streamlit UI   (app.py, requirements.txt, Dockerfile)
```

## API (port 7860)

| Endpoint | Method | Input | Output |
|---|---|---|---|
| `/` | GET | – | health check |
| `/v1/predict` | POST | JSON object with the 10 features | `{"Predicted Product_Store_Sales_Total": 2894.66}` |
| `/v1/predictbatch` | POST | CSV upload in form field `file` | `{"0": 4058.68, "1": 3380.21, ...}` |

Features: `Product_Weight`, `Product_Sugar_Content`, `Product_Allocated_Area`, `Product_MRP`, `Store_Size`,
`Store_Location_City_Type`, `Store_Type`, `Product_Id_char`, `Store_Age_Years`, `Product_Type_Category`.

## Run (e.g. in GitHub Codespaces)

```bash
docker network create superkart-network

docker build -t superkart-backend ./backend_files
docker run -d --name backend --network superkart-network -p 7860:7860 superkart-backend

docker build -t superkart-frontend ./frontend_files
docker run -d --name frontend --network superkart-network -p 8501:8501 superkart-frontend
```

The frontend reaches the backend at `http://backend:7860` over the Docker network (override with `-e BACKEND_URL=...`).
In Codespaces, set ports 7860 and 8501 to **Public** in the Ports tab and open the forwarded URL of port 8501.
