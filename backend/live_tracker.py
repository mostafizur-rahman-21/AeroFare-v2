import os
import csv
import requests
from datetime import datetime

SERPAPI_KEY = "0f16ee52dc6b646b76b0ce5a88094dd6bf1bc97bef6ce40649ac69adad3f0b80"

# Store live price logs outside the VS Code workspace so Live Server never reloads
DATA_DIR = os.path.expanduser("~/aerofare_data")
os.makedirs(DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(DATA_DIR, "live_prices_history.csv")

CITY_TO_IATA = {
    "Delhi": "DEL",
    "Mumbai": "BOM",
    "Bangalore": "BLR",
    "Kolkata": "CCU",
    "Hyderabad": "HYD",
    "Chennai": "MAA"
}


def get_live_flight_offers(
    source_city: str,
    destination_city: str,
    travel_date: str,
    flight_class: str = "Economy",
    stops_num: int = None
):
    dep_code = CITY_TO_IATA.get(source_city)
    arr_code = CITY_TO_IATA.get(destination_city)

    if not dep_code or not arr_code or not SERPAPI_KEY or SERPAPI_KEY == "PASTE_YOUR_SERPAPI_KEY_HERE":
        return []

    travel_class_code = 3 if flight_class == "Business" else 1

    params = {
        "engine": "google_flights",
        "departure_id": dep_code,
        "arrival_id": arr_code,
        "outbound_date": travel_date,
        "currency": "INR",
        "hl": "en",
        "type": "2",
        "travel_class": travel_class_code,
        "api_key": SERPAPI_KEY
    }

    # SerpApi Google Flights stops filter: 1 = Nonstop only
    if stops_num == 0:
        params["stops"] = "1"

    try:
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=10)
        data = response.json()

        flights = data.get("best_flights", []) + data.get("other_flights", [])
        live_results = []

        for item in flights:
            price = item.get("price")
            first_leg = item.get("flights", [{}])[0]
            airline_name = first_leg.get("airline", "Unknown")
            duration = item.get("total_duration", 140)
            stops = min(max(0, len(item.get("flights", [])) - 1), 2)

            if price and (stops_num is None or stops == stops_num):
                live_results.append({
                    "airline": airline_name,
                    "live_price": float(price),
                    "duration_mins": int(duration),
                    "stops_num": stops
                })

        live_results.sort(key=lambda x: x["live_price"])
        return live_results

    except Exception as e:
        print("Live API fetch error:", e)
        return []

def log_live_price_for_retraining(row_dict: dict, live_price: float):
    """Appends fetched live prices to ~/aerofare_data/live_prices_history.csv."""
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "timestamp", "airline", "source_city", "destination_city",
                "departure_time", "arrival_time", "class", "stops_num",
                "duration_mins", "days_left", "price"
            ])
        writer.writerow([
            datetime.now().isoformat(),
            row_dict["airline"],
            row_dict["source_city"],
            row_dict["destination_city"],
            row_dict["departure_time"],
            row_dict["arrival_time"],
            row_dict["class"],
            row_dict["stops_num"],
            row_dict["duration_mins"],
            row_dict["days_left"],
            live_price
        ])