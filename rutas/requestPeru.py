# Remember, Install pip install requests


import json
import requests

API_URL = "https://www.geoboundaries.org/api/current/gbOpen/PER/ADM1/"
TARGET_REGIONS = {"Arequipa", "Moquegua", "Puno", "Cusco"}

# Get the dataset metadata and GeoJSON URL
response = requests.get(API_URL, timeout=30)
response.raise_for_status()
metadata = response.json()[0]

geojson_url = metadata["gjDownloadURL"]

# Download the GeoJSON
response = requests.get(geojson_url, timeout=120)
response.raise_for_status()
geojson = response.json()

# Match region names in the feature properties
selected_features = []
for feature in geojson.get("features", []):
    properties = feature.get("properties", {})
    property_values = {
        str(value).strip()
        for value in properties.values()
        if value is not None
    }

    if property_values & TARGET_REGIONS:
        selected_features.append(feature)

if not selected_features:
    raise ValueError(
        "No matching regions found. Check the feature property names and values."
    )

# Save the selected features as a GeoJSON FeatureCollection
output = {
    "type": "FeatureCollection",
    "features": selected_features,
}

output_path = "southern_peru_regions.geojson"
with open(output_path, "w", encoding="utf-8") as file:
    json.dump(output, file, ensure_ascii=False)

print(f"Saved {len(selected_features)} regions to {output_path}")
