from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
import pandas as pd
import joblib

from live_tracker import get_live_flight_offers, log_live_price_for_retraining

app = FastAPI(title="AeroFare Hybrid ML + Live Price API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load trained ML model and 29 columns once at startup
model = joblib.load("aerofare_model.joblib")
model_columns = joblib.load("model_columns.joblib")

ALL_AIRLINES = ["Air_India", "AirAsia", "GO_FIRST", "IndiGo", "SpiceJet", "Vistara"]


class FlightSearch(BaseModel):
    airline: str
    source_city: str
    destination_city: str
    departure_time: str = "Morning"
    arrival_time: str = "Evening"
    flight_class: str = Field(default="Economy", alias="class")
    stops_num: int = 0
    duration_mins: int = 140
    travel_date: Optional[str] = None
    days_left: Optional[int] = None

    class Config:
        populate_by_name = True


def normalize_airline(name: str) -> str:
    return name.lower().replace("_", "").replace(" ", "").replace("-", "").strip()


def predict_ml_fare(row_dict: dict) -> float:
    df = pd.DataFrame([row_dict])
    df_encoded = pd.get_dummies(df).reindex(columns=model_columns, fill_value=0)
    return round(float(model.predict(df_encoded)[0]), 2)


def compute_days_left(search: FlightSearch) -> int:
    if search.travel_date:
        travel_dt = datetime.strptime(search.travel_date, "%Y-%m-%d").date()
        return max(1, (travel_dt - date.today()).days)
    if search.days_left is not None:
        return max(1, search.days_left)
    return 10


def build_analytics_arrays(base_input: dict):
    airline_comparison = []
    for airline_name in ALL_AIRLINES:
        temp = base_input.copy()
        temp["airline"] = airline_name
        airline_comparison.append({
            "airline": airline_name.replace("_", " "),
            "price": predict_ml_fare(temp)
        })
    airline_comparison.sort(key=lambda x: x["price"])

    booking_trend = []
    for d in [1, 3, 7, 14, 21, 30, 45]:
        temp = base_input.copy()
        temp["days_left"] = d
        booking_trend.append({
            "days_left": d,
            "price": predict_ml_fare(temp)
        })

    return airline_comparison, booking_trend


@app.get("/")
def health_check():
    return {"status": "AeroFare Hybrid ML + Live Engine Ready"}


@app.post("/predict")
@app.post("/predict/")
def predict_only(search: FlightSearch):
    days_left = compute_days_left(search)
    base_input = {
        "airline": search.airline,
        "source_city": search.source_city,
        "destination_city": search.destination_city,
        "departure_time": search.departure_time,
        "arrival_time": search.arrival_time,
        "class": search.flight_class,
        "stops_num": search.stops_num,
        "duration_mins": search.duration_mins,
        "days_left": days_left,
    }

    ml_predicted_price = predict_ml_fare(base_input)
    airline_comparison, booking_trend = build_analytics_arrays(base_input)

    return {
        "days_left": days_left,
        "selected_airline": search.airline.replace("_", " "),
        "predicted_price": ml_predicted_price,
        "ml_predicted_price": ml_predicted_price,
        "live_lowest_price": None,
        "market_cheapest_offer": None,
        "price_difference_inr": 0.0,
        "price_difference_percent": 0.0,
        "ai_verdict": "Historical fare analysis complete.",
        "top_5_live_flights": [],
        "airline_comparison": airline_comparison,
        "booking_trend": booking_trend
    }


@app.post("/analyze")
@app.post("/analyze/")
def analyze_live_vs_ml(search: FlightSearch):
    days_left = compute_days_left(search)
    display_airline = search.airline.replace("_", " ")
    target_norm = normalize_airline(search.airline)

    base_input = {
        "airline": search.airline,
        "source_city": search.source_city,
        "destination_city": search.destination_city,
        "departure_time": search.departure_time,
        "arrival_time": search.arrival_time,
        "class": search.flight_class,
        "stops_num": search.stops_num,
        "duration_mins": search.duration_mins,
        "days_left": days_left,
    }

    # 1. Historical ML Analysed Price for the selected airline
    ml_predicted_price = predict_ml_fare(base_input)
    airline_comparison, booking_trend = build_analytics_arrays(base_input)

    # 2. Fetch live flights for route & date
    all_live_offers = []
    if search.travel_date:
        all_live_offers = get_live_flight_offers(
            search.source_city,
            search.destination_city,
            search.travel_date,
            search.flight_class,
            stops_num=search.stops_num
        )

    # Filter specifically for the user's selected airline
    selected_airline_offers = [
        offer for offer in all_live_offers
        if target_norm in normalize_airline(offer["airline"])
        or normalize_airline(offer["airline"]) in target_norm
    ]

    market_cheapest = all_live_offers[0] if all_live_offers else None

    # Case A: Selected airline has NO live flights on this date
    if not selected_airline_offers:
        alt_note = (
            f" Cheapest available carrier on this date is {market_cheapest['airline']} at ₹{market_cheapest['live_price']:,.0f}."
            if market_cheapest else ""
        )
        return {
            "days_left": days_left,
            "selected_airline": display_airline,
            "predicted_price": ml_predicted_price,
            "ml_predicted_price": ml_predicted_price,
            "live_lowest_price": None,
            "market_cheapest_offer": market_cheapest,
            "price_difference_inr": None,
            "price_difference_percent": None,
            "ai_verdict": f"No live {display_airline} flight available on this date — Change date.{alt_note}",
            "top_5_live_flights": all_live_offers[:5],
            "airline_comparison": airline_comparison,
            "booking_trend": booking_trend
        }

    # Case B: Compare selected airline's live fare against selected airline's analysed historical fare
    lowest_selected_live = selected_airline_offers[0]["live_price"]
    log_live_price_for_retraining(base_input, lowest_selected_live)

    diff_amount = round(lowest_selected_live - ml_predicted_price, 2)
    diff_percent = round((diff_amount / ml_predicted_price) * 100, 1)

    if diff_percent <= -10:
        verdict = f"GREAT DEAL on {display_airline}! Live fare is {abs(diff_percent)}% (₹{abs(diff_amount):,.0f}) cheaper than historical norm. Book now!"
    elif diff_percent >= 10:
        verdict = f"SURGE ALERT on {display_airline}! Live fare is {diff_percent}% (₹{diff_amount:,.0f}) higher than historical norm. Consider shifting dates."
    else:
        verdict = f"FAIR PRICE on {display_airline}! Live fare matches historical analysed trend ({diff_percent:+}%)."

    # Prioritize selected airline flights at top of table, followed by other live options
    other_offers = [o for o in all_live_offers if o not in selected_airline_offers]
    ordered_offers = (selected_airline_offers + other_offers)[:6]

    return {
        "days_left": days_left,
        "selected_airline": display_airline,
        "predicted_price": ml_predicted_price,
        "ml_predicted_price": ml_predicted_price,
        "live_lowest_price": lowest_selected_live,
        "market_cheapest_offer": market_cheapest,
        "price_difference_inr": diff_amount,
        "price_difference_percent": diff_percent,
        "ai_verdict": verdict,
        "top_5_live_flights": ordered_offers,
        "airline_comparison": airline_comparison,
        "booking_trend": booking_trend
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)