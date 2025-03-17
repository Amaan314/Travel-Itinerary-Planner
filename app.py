import streamlit as st
import requests
from langchain_groq import ChatGroq 
import json

st.set_page_config(
    page_title="Trip Planner Agent",
    page_icon="🏖️",
    layout="centered",
    initial_sidebar_state="auto"
)

GROK_API_KEY = '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'
chat_groq = ChatGroq(api_key=GROK_API_KEY, model="llama-3.3-70b-versatile")
SERPER_API_KEY = '001233b4cc8672f2bd624b5d7bdbc5e9e0122c7d'
SERPER_API_ENDPOINT = "https://google.serper.dev/search"

custom_css = """
<style>
body {
    background-color: #f4f4f4;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.sidebar .sidebar-content {
    background-image: linear-gradient(#2C3E50, #4CA1AF);
    color: white;
}
.stButton>button {
    background-color: #4CA1AF;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 0.5em 1em;
}
.stButton>button:hover {
    background-color: #2C3E50;
    color: white;
}
.itinerary-title {
    font-size: 1.5em;
    margin-bottom: 0.5em;
    color: #2C3E50;
}
.activity-item {
    background-color: #170303;
    padding: 0.75em;
    margin-bottom: 0.5em;
    border-radius: 5px;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

def clean_json_string(raw_str: str) -> str:
    raw_str = raw_str.strip()
    if raw_str.startswith("```"):
        lines = raw_str.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return raw_str

def get_travel_itinerary(origin, destination, start_date, end_date, preferences):
    prompt = (
       f"Generate a detailed travel itinerary for a trip starting from {origin} to {destination}"
        f"from {start_date} to {end_date}. "
        f"Include activities that match these travel preferences: {preferences}. "
        "Output the itinerary in valid JSON format where each key is a day number "
        "and each value is a list of activities. Each activity should be a JSON object with keys: activity, time, and description."
    )
    result = chat_groq.invoke(prompt)
    if hasattr(result, 'content'):
        result_str = result.content
    else:
        result_str = result

    # st.write("Raw output:", result_str)  

    clean_result = clean_json_string(result_str)

    try:
        itinerary_data = json.loads(clean_result)
    except json.JSONDecodeError:
        st.error("Failed to decode itinerary data. Please try again or adjust your input.")
        itinerary_data = None
    return itinerary_data

def get_local_attractions(destination):
    query = f"top attractions in {destination}"
    params = {"q": query}
    headers = {"X-API-KEY": SERPER_API_KEY}
    
    try:
        response = requests.get(SERPER_API_ENDPOINT, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching local attractions: {e}")
        return None

def display_itinerary(itinerary_data):
    st.markdown("<p class='itinerary-title'>Your Itinerary</p>", unsafe_allow_html=True)
    if not itinerary_data:
        st.write("No itinerary data found.")
        return
    for day, activities in itinerary_data.items():
        st.markdown(f"**Day {day}:**")
        if isinstance(activities, list):
            for activity in activities:
                if isinstance(activity, dict):
                    act = activity.get("activity", "No activity")
                    time = activity.get("time", "No time")
                    desc = activity.get("description", "")
                    st.markdown(f"<div class='activity-item'><strong>{act}</strong> at {time}<br>{desc}</div>", unsafe_allow_html=True)
                else:
                    st.write(f"- {activity}")
        else:
            st.write(activities)

def display_local_attractions(search_results):
    st.subheader("Local Attractions")
    organic_results = search_results.get("organic", [])
    if not organic_results:
        st.write("No attractions found.")
        return
    for result in organic_results[:5]:
        title = result.get("title", "No title")
        link = result.get("link", "#")
        snippet = result.get("snippet", "")
        st.markdown(f"**[{title}]({link})**")
        st.write(snippet)

# -------------------------
# Streamlit UI with Sidebar and Tabs
# -------------------------
def main():
    st.header("✈️ 🎫 :red[Trip Planner] :green[Agent] 🏝️ 🗺️",divider= 'rainbow')
    st.sidebar.title("✈️ 🎫 Trip Planner Agent 🏝️ 🗺️")
    origin = st.sidebar.text_input("From", placeholder="Mumbai, Maharashtra, India", help="Enter your starting location.")
    destination = st.sidebar.text_input("Destination", placeholder="Kolkata, West Bengal, India", help="Enter the city or country you plan to visit.")
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")
    preferences = st.sidebar.text_area("Travel Preferences", placeholder='Adventure, Relaxation', help="Share your travel style: adventure, relaxation, culture, food, etc.")
    
    if st.sidebar.button("Generate Itinerary"):
        if destination and start_date and end_date:
            with st.spinner("Generating your itinerary..."):
                itinerary_data = get_travel_itinerary(origin, destination, start_date.isoformat(), end_date.isoformat(), preferences)
                if itinerary_data:
                    st.session_state.itinerary_data = itinerary_data
                else:
                    st.error("Failed to generate itinerary.")
        else:
            st.error("Please fill in all required fields in the sidebar.")
    
    if st.sidebar.button("Show Local Attractions"):
        if destination:
            with st.spinner("Fetching local attractions..."):
                search_results = get_local_attractions(destination)
                if search_results:
                    st.session_state.search_results = search_results
                else:
                    st.error("Failed to fetch local attractions.")
        else:
            st.error("Please enter a destination in the sidebar.")

    tab1, tab2 = st.tabs(["Itinerary", "Local Attractions"])
    with tab1:
        if "itinerary_data" in st.session_state:
            display_itinerary(st.session_state.itinerary_data)
        else:
            st.info("Your itinerary will appear here after generation.")
    with tab2:
        if "search_results" in st.session_state:
            display_local_attractions(st.session_state.search_results)
        else:
            st.info("Local attractions will appear here after fetching.")
    st.sidebar.markdown(
        """
        🚀 Created by : [**AP**](https://www.linkedin.com/in/amaan-poonawala/)
        """,
            unsafe_allow_html=True
        )
if __name__ == "__main__":
    main()