from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.neighbors import NearestNeighbors
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize the FastAPI app
app = FastAPI(title="Wine Suggestion API", version="1.0")

def load_wine_data():
    path_to_file = 'fozzy_dataframe.bin'
    with open(path_to_file, 'rb') as file_object:
        raw_data = file_object.read()
    wine_df = pickle.loads(raw_data)
    return wine_df

wine_data = load_wine_data()

# Preprocess wine data and build KNN model
def preprocess_wine_data(wine_data):
    scaler = MinMaxScaler()
    wine_data['price_normalized'] = scaler.fit_transform(wine_data[['price_uah']])
    encoder = OneHotEncoder()
    encoded_features = np.hstack([
        encoder.fit_transform(wine_data[['country']]).toarray(),
        encoder.fit_transform(wine_data[['region']]).toarray(),
        encoder.fit_transform(wine_data[['variety']]).toarray(),
        encoder.fit_transform(wine_data[['color']]).toarray(),
        encoder.fit_transform(wine_data[['type']]).toarray(),
        encoder.fit_transform(wine_data[['sugar']]).toarray()
    ])
    weighted_features = np.hstack([
        wine_data['price_normalized'].values.reshape(-1, 1) * 40,
        encoded_features
    ])
    wine_data['feature_vector'] = list(weighted_features)
    return wine_data, weighted_features

def build_knn_model(weighted_features):
    knn_model = NearestNeighbors(n_neighbors=30, metric='cosine')
    knn_model.fit(weighted_features)
    return knn_model

wine_data, weighted_features = preprocess_wine_data(wine_data)
knn_model = build_knn_model(weighted_features)

# API Models
class WineSuggestionRequest(BaseModel):
    wine_name: str
    n_results: int = 10

@app.get("/wines", response_model=list)
def list_wines(variety: str = None, region: str = None, country: str = None, limit: int = 50):
    """
    List wines with optional filters for variety, region, and country.
    """
    filtered_data = wine_data.copy()

    if variety:
        filtered_data = filtered_data[filtered_data['variety'] == variety]
    if region:
        filtered_data = filtered_data[filtered_data['region'] == region]
    if country:
        filtered_data = filtered_data[filtered_data['country'] == country]

    # Select the required fields
    filtered_data = filtered_data[[
        "title", "wine_name", "producer", "country", "gw_rating", "price_uah",
        "href", "vintage", "color", "type", "region", "variety", "alcohol",
        "sugar", "image_src", "sku", "name5", "tasteES"
    ]]

    # Handle invalid JSON values
    filtered_data = filtered_data.replace([np.inf, -np.inf], None)  # Replace infinities with None
    filtered_data = filtered_data.fillna("")  # Replace NaN with an empty string

    # Limit the number of rows and convert to JSON-compatible format
    return filtered_data.head(limit).to_dict(orient="records")
    

# API Endpoints
@app.get("/suggestions", response_model=list)
def suggest_wines(
    wine_name: str = Query(..., description="The name of the wine to base suggestions on"),
    n_results: int = Query(10, description="Number of similar wines to return")
):
    """
    Suggest similar wines based on a given wine name.
    """
    # Check if the selected wine exists
    if wine_name not in wine_data['title'].values:
        raise HTTPException(status_code=404, detail="Wine not found")

    # Normalize 'price_uah' and 'alcohol'
    scaler = MinMaxScaler()
    wine_data['price_normalized'] = scaler.fit_transform(wine_data[['price_uah']])

    # One-hot encoding for categorical features
    encoder = OneHotEncoder()
    encoded_country = encoder.fit_transform(wine_data[['country']]).toarray()
    encoded_region = encoder.fit_transform(wine_data[['region']]).toarray()
    encoded_variety = encoder.fit_transform(wine_data[['variety']]).toarray()
    encoded_color = encoder.fit_transform(wine_data[['color']]).toarray()
    encoded_type = encoder.fit_transform(wine_data[['type']]).toarray()
    encoded_sugar = encoder.fit_transform(wine_data[['sugar']]).toarray()

    # Assign weights
    weights = {
        'price': 40, 'country': 10, 'region': 40, 'variety': 40,
        'color': 10, 'type': 50, 'sugar': 35, 'review_vector': 3
    }

    # Apply weights to features
    weighted_price = wine_data['price_normalized'].values.reshape(-1, 1) * weights['price']
    weighted_features = np.hstack((
        weighted_price,
        encoded_country * weights['country'],
        encoded_region * weights['region'],
        encoded_variety * weights['variety'],
        encoded_color * weights['color'],
        encoded_type * weights['type'],
        encoded_sugar * weights['sugar']
    ))

    # Review vector and combined features
    review_vectors = np.array([np.array(vec).flatten() for vec in wine_data['review_vector']])
    scaled_review_vectors = review_vectors * weights['review_vector']
    combined_vectors = np.hstack((scaled_review_vectors, weighted_features))
    wine_data['combined_vector'] = list(combined_vectors)

    # Create KNN model
    knn_model = NearestNeighbors(n_neighbors=30, algorithm='brute', metric='cosine')
    knn_model.fit(combined_vectors)

    # Find similar wines
    wine_vector = combined_vectors[wine_data['title'] == wine_name][0]
    distances, indices = knn_model.kneighbors([wine_vector], n_neighbors=n_results)

    # Retrieve and process similar wines
    result_df = wine_data.iloc[indices[0]].copy()
    result_df['similarity_score'] = (1 - distances[0]) * 100

    # Handle invalid JSON values
    numeric_columns = result_df.select_dtypes(include=[np.number]).columns
    if result_df[numeric_columns].isnull().any().any():
        logger.warning("Detected NaN values in numeric columns. Filling with default values.")
    if (result_df[numeric_columns] == np.inf).any().any() or (result_df[numeric_columns] == -np.inf).any().any():
        logger.warning("Detected infinite values in numeric columns. Replacing with None.")

    result_df[numeric_columns] = result_df[numeric_columns].replace([np.inf, -np.inf], None)  # Replace infinities with None
    result_df = result_df.fillna("")  # Replace NaN with an empty string

    # Return relevant fields
    return result_df[[
        "title", "price_uah", "region", "variety", "color", "type", "similarity_score"
    ]].to_dict(orient="records")


@app.get("/filters", response_model=dict)
def get_filters():
    """
    Get unique filter options for variety, region, and country.
    """
    return {
        "varieties": wine_data['variety'].dropna().unique().tolist(),
        "regions": wine_data['region'].dropna().unique().tolist(),
        "countries": wine_data['country'].dropna().unique().tolist()
    }