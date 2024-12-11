# Wine Suggestion API

A FastAPI-based application that suggests wines based on similarity and provides filter options for wine attributes. This API processes a dataset of wines (fozzy_dataframe.bin) and utilizes a K-Nearest Neighbors (KNN) model for recommendations.

## Features

- Retrieve filter options for `variety`, `region`, and `country`.
- List available wines by `variety`, `region`, and `country`.
- Suggest similar wines based on a given wine title.

---

## Requirements
- Python 3.8+
- Pip (Python package manager)

---

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/voatsap/panda-api.git
   cd panda-api
   ```

2. **Create a Virtual Environment**

   - On Linux/Mac:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. **Start the API**
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

---

## API Endpoints

### 1. **Get Available Filters**

Retrieve unique filter options for wine attributes such as `variety`, `region`, and `country`.

#### Endpoint:
```http
GET /filters
```
```bash
curl -X 'GET' \
  'http://localhost:8000/filters' \
  -H 'accept: application/json'
```
Example output:
```json
{
    "varieties": [
        "Sauvignon Blanc",
        "Chardonnay",
        "Blend",
        "White Muscat",
        "Sangiovese"
    ],
    "regions": [
        "Crimea",
        "Central Valley",
        "Cava",
        "Asti",
        "Tuscany"
    ],
    "countries": [
        "Ukraine",
        "Chile",
        "Spain",
        "Italy",
        "France"
    ]
}
```

### 2. **List Wines**

Fetch a list of wines based on optional filters such as variety, region, and country. You can limit the number of results.


#### Endpoint:
```http
GET /wines
```
```bash
curl -X 'GET' \
  'http://localhost:8000/wines?variety=Chardonnay&country=France&limit=50' \
  -H 'accept: application/json'
```
Example output:
```json
{
    "title": "Louis Latour Chablis La Chanfleure Louis Latour",
    "wine_name": "Louis Latour Chablis La Chanfleure",
    "producer": "Louis Latour",
    "country": "France",
    "gw_rating": "3.9",
    "price_uah": 47.24,
    "href": "https://www.vivino.com/US-CA/en/louis-latour-chablis-la-chanfleure/w/7236",
    "vintage": "",
    "color": "white",
    "type": "white",
    "region": "Chablis",
    "variety": "Chardonnay",
    "alcohol": 12.5,
    "sugar": "0–0,3",
    "image_src": "https://content.silpo.ua/sku/ecommerce/15/720x720/158430_720x720_f564bc51-da26-d983-fa5b-cdd4502a89fb.png",
    "sku": 158430,
    "name5": "Still white wines",
    "tasteES": "dry"
},
{
    "title": "Perrier-Jouet Grand Brut Perrier-Jouët",
    "wine_name": "Perrier-Jouet Grand Brut",
    "producer": "Perrier-Jouët",
    "country": "France",
    "gw_rating": "4.2",
    "price_uah": 68.67,
    "href": "https://www.vivino.com/US-CA/en/perrier-jouet-grand-brut-champagne/w/79160",
    "vintage": "",
    "color": "white",
    "type": "sparkling",
    "region": "Champagne",
    "variety": "Chardonnay",
    "alcohol": 12,
    "sugar": "0–0,3",
    "image_src": "https://content.silpo.ua/sku/ecommerce/24/720x720/243564_720x720_01e43121-56ed-d5b5-8555-3bd75cfd44b3.png",
    "sku": 243564,
    "name5": "Sparkling alcoholic wines",
    "tasteES": "dry"
}
```

### 3. **Suggest Similar Wines**

Find wines similar to a given wine based on its attributes.

#### Endpoint:
```http
GET /suggestions
```
```bash
curl -X 'GET' \
  'http://localhost:8000/suggestions?wine_name=Pascal%20Bouchard%20Bourgogne%20Chardonnay%20Pascal%20Bouchard&n_results=10' \
  -H 'accept: application/json'
```
Example output:
```json
{
    "title": "Pascal Bouchard Bourgogne Chardonnay Pascal Bouchard",
    "price_uah": 21.8,
    "region": "Burgundy",
    "variety": "Chardonnay",
    "color": "white",
    "type": "white",
    "similarity_score": 100
},
{
    "title": "Louis Max Bourgogne Chardonnay Beaucharme Louis Max",
    "price_uah": 6.99,
    "region": "Burgundy",
    "variety": "Chardonnay",
    "color": "white",
    "type": "white",
    "similarity_score": 96.30948880360044
},
{
    "title": "Domaine Anne Gros Bourgogne Chardonnay white Anne Gros Estate",
    "price_uah": 43.6,
    "region": "Burgundy",
    "variety": "Chardonnay",
    "color": "white",
    "type": "white",
    "similarity_score": 96.2343778612493
}
```

### Access the API Documentation

	•	Swagger UI: http://localhost:8000/docs