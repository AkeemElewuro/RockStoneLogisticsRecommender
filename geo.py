#import subprocess
#import sys

# Install required packages
#def install_packages():
#    packages = ["pandas", "folium", "streamlit", "streamlit-folium", "googlemaps", "geopy"]
#    for package in packages:
#        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

#install_packages()

# Import libraries after installation
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import folium_static
import googlemaps
from geopy.distance import geodesic

# Replace local CSV path with a public URL
CSV_URL = "https://github.com/AkeemElewuro/RockStoneLogisticsRecommender/blob/main/geocoded_data.csv"
API_KEY = "AIzaSyCxMDrxcYW2Q5CMtqmm9TOlSi0iAVYhDJ0"

def load_data():
    """Load geocoded data from a shared or public URL."""
    try:
        return pd.read_csv(CSV_URL, encoding='ISO-8859-1', on_bad_lines='skip')
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def main():
    # Page configuration
    st.set_page_config(page_title="Logistics Carrier Recommender", layout="wide")

    # Initialize Google Maps client
    try:
        gmaps_client = googlemaps.Client(key=API_KEY)
    except Exception as e:
        st.error(f"Google Maps client error: {e}")
        return

    # Load carrier data
    geocoded_data = load_data()
    if geocoded_data.empty:
        st.warning("No carrier data available.")
        return

    # UI
    st.title("Logistics Carrier Recommender")
    user_address = st.text_input("Enter your pickup address:")
    
    if user_address:
        try:
            # Geocode user address
            geocode_result = gmaps_client.geocode(user_address)
            if not geocode_result:
                st.error("Could not geocode the provided address.")
                return

            user_location = {
                'lat': geocode_result[0]['geometry']['location']['lat'],
                'long': geocode_result[0]['geometry']['location']['lng']
            }

            # Find closest carriers
            closest_carriers = get_closest_carriers(user_location, geocoded_data)
            
            if not closest_carriers.empty:
                st.subheader("Closest Carriers")
                st.dataframe(closest_carriers[['carrier_name', 'state', 'address', 'distance']])

                # Generate map
                m = generate_map(closest_carriers, user_location)
                if m:
                    folium_static(m)
            else:
                st.warning("No carriers found near your location.")

        except Exception as e:
            st.error(f"An error occurred: {e}")

def get_closest_carriers(user_location, geocoded_data, n=3):
    """Find closest carriers."""
    try:
        user_coords = (user_location['lat'], user_location['long'])
        
        def calculate_distance(row):
            try:
                return geodesic(user_coords, (row['lat'], row['long'])).kilometers
            except Exception:
                return float('inf')
        
        geocoded_data['distance'] = geocoded_data.apply(calculate_distance, axis=1)
        closest_carriers = geocoded_data.nsmallest(n, 'distance')
        
        return closest_carriers[['carrier_name', 'state', 'address', 'lat', 'long', 'distance']]
    except Exception as e:
        st.error(f"Error finding closest carriers: {e}")
        return pd.DataFrame()

def generate_map(carriers_data, user_location):
    """Generate map with carrier locations."""
    try:
        center_lat = user_location['lat']
        center_lng = user_location['long']
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
        
        # User location marker
        folium.Marker(
            [user_location['lat'], user_location['long']],
            popup="Your Location",
            icon=folium.Icon(color="red", icon="home"),
            tooltip="Your Location"
        ).add_to(m)
        
        # Carrier markers
        for _, row in carriers_data.iterrows():
            popup_text = f"""
                <b>{row['carrier_name']}</b><br>
                State: {row['state']}<br>
                Address: {row['address']}<br>
                Distance: {row['distance']:.2f} km
            """
            folium.Marker(
                [row['lat'], row['long']],
                popup=folium.Popup(popup_text, max_width=300),
                icon=folium.Icon(color="blue", icon="truck"),
                tooltip=row['carrier_name']
            ).add_to(m)
        
        # Coverage circle
        folium.Circle(
            [center_lat, center_lng],
            radius=5000,  # 5km radius
            color="green",
            fill=True,
            fill_opacity=0.1
        ).add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Map generation error: {e}")
        return None

if __name__ == "__main__":
    main()
