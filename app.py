
import streamlit as st
import openai
import requests

# הגדרות ראשוניות
st.set_page_config(page_title="SmartFly2", page_icon="✈️")
st.title("✈️ SmartFly2 – חיפוש טיסות חכם בעברית")

# קלט מהמשתמש
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("כתוב כאן את השאילתה שלך (לדוגמה: טיסה ללונדון בתחילת יולי עם מזוודה)")

# הצגת שיחה קודמת
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(msg)

if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        st.markdown("🔄 מעבד את השאילתה...")

    # שליחת שאילתה ל-GPT
    try:
        gpt_response = openai.ChatCompletion.create(
            model="ft:gpt-3.5-turbo-0125:personal::BNK4ZNHh",
            messages=[{"role": "user", "content": user_input}]
        )
        parsed = eval(gpt_response["choices"][0]["message"]["content"])

        # שליחת השאילתה לאמדאוס
        token_response = requests.post(
            "https://api.amadeus.com/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": st.secrets["AMADEUS_CLIENT_ID"],
                "client_secret": st.secrets["AMADEUS_CLIENT_SECRET"]
            }
        )
        token = token_response.json()["access_token"]

        flight_response = requests.post(
            "https://api.amadeus.com/v2/shopping/flight-offers",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "currencyCode": "USD",
                "originDestinations": [{
                    "id": "1",
                    "originLocationCode": parsed.get("origin"),
                    "destinationLocationCode": parsed.get("destination"),
                    "departureDateTimeRange": {"date": parsed.get("date")}
                }],
                "travelers": [{"id": "1", "travelerType": "ADULT"}],
                "sources": ["GDS"],
                "searchCriteria": {"maxFlightOffers": 5}
            }
        )

        flights = flight_response.json().get("data", [])
        if not flights:
            answer = "לא נמצאו טיסות מתאימות."
        else:
            answer = "מצאתי עבורך את הטיסות הבאות:\n"
            for f in flights:
                seg = f["itineraries"][0]["segments"][0]
                dep_date = seg["departure"]["at"].split("T")[0]
                price = f["price"]["grandTotal"]
                answer += f"- {seg['departure']['iataCode']} → {seg['arrival']['iataCode']} בתאריך {dep_date}, מחיר: {price} USD\n"

    except Exception as e:
        answer = f"שגיאה בעיבוד: {str(e)}"

    st.session_state.chat_history.append(("assistant", answer))
    with st.chat_message("assistant"):
        st.markdown(answer)
