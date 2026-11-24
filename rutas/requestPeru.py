# Remember, Install pip install requests

import json
from pathlib import Path

API_URL = "https://www.geoboundaries.org/api/current/gbOpen/PER/ADM1/"
TARGET_REGIONS = {"Arequipa", "Moquegua", "Puno", "Cusco"}
OUTPUT_PATH = Path(__file__).with_name("southern_peru_regions.geojson")


def descargar_regiones(output_path=OUTPUT_PATH):
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        metadata = response.json()
        print(metadata)
        if isinstance(metadata, list):
            metadata = metadata[0]

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Connection Error: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"An error occurred: {err}")


    except ImportError:
        raise ImportError("La librería 'requests' no está instalada. Ejecuta: pip install requests")

    geojson_url = metadata["gjDownloadURL"]

    response = requests.get(geojson_url, timeout=120)
    response.raise_for_status()
    geojson = response.json()

    print("El mapa es :", geojson)

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

    output = {
        "type": "FeatureCollection",
        "features": selected_features,
    }

    output_path = Path(output_path)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False)

    print(f"Saved {len(selected_features)} regions to {output_path}")
    return output_path


if __name__ == "__main__":
    descargar_regiones()
