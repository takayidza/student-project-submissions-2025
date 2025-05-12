import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from maize_health_analyzer import MaizeHealthAnalyzerImproved
from datetime import datetime
from PIL import Image
import io
import requests
import time
import firebase_admin
from firebase_admin import credentials, firestore, auth
import base64

# Set page configuration
st.set_page_config(
    page_title="Maize Health Monitoring Dashboard",
    page_icon="🌽",
    layout="wide"
)

# --- Firebase Setup ---
CREDENTIALS_PATH = "firebase-credentials.json"

if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        st.sidebar.success("Connected to Firebase!")
    except Exception as e:
        st.sidebar.error(f"Failed to connect to Firebase: {e}")
        db = None
else:
    db = firestore.client()

# Initialize session state for authentication
if 'user_authenticated' not in st.session_state:
    st.session_state.user_authenticated = False

if 'user_id' not in st.session_state:
    st.session_state.user_id = None

if 'user_email' not in st.session_state:
    st.session_state.user_email = None

if 'login_error' not in st.session_state:
    st.session_state.login_error = None

# Authentication functions
def login_user(email, password):
    try:
        # Use Firebase Admin SDK to verify the user
        user = auth.get_user_by_email(email)
        # We can't directly verify passwords with Admin SDK
        # In a production app, use Firebase Auth REST API or Firebase Auth UI
        # This is a simplified example for demonstration
        
        # For demo purposes, we'll assume password is correct if user exists
        # In production, use Firebase Authentication client SDK for password verification
        st.session_state.user_authenticated = True
        st.session_state.user_id = user.uid
        st.session_state.user_email = user.email
        st.session_state.login_error = None
        return True
    except Exception as e:
        st.session_state.login_error = f"Login failed: {str(e)}"
        return False

def logout_user():
    st.session_state.user_authenticated = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.login_error = None

# Login Page
def show_login_page():
    st.title("🌽 Maize Crop Health Monitoring System")
    st.header("Login")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")
        
        if login_button:
            if login_user(email, password):
                st.rerun()
            else:
                st.error(st.session_state.login_error)
    
    with col2:
        st.info("Please log in to access the Maize Health Monitoring Dashboard.")
        st.markdown("""
        This system allows you to:
        - Upload and analyze maize crop images
        - Set up continuous capture from ESP32 cameras
        - View analysis results with detailed health metrics
        - Track historical data trends
        """)

# Main application after authentication
def show_main_application():
    # Application title
    st.title("🌽 Maize Crop Health Monitoring System")
    
    # Display user info in sidebar
    st.sidebar.success(f"Logged in as: {st.session_state.user_email}")
    if st.sidebar.button("Logout"):
        logout_user()
        st.rerun()

    # Sidebar navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to", ["Upload & Analyze", "Continuous Capture", "View Results", "Historical Data"])

    # Initialize session state
    if 'results_df' not in st.session_state:
        st.session_state.results_df = pd.DataFrame()
        if os.path.exists("analysis_results.csv"):
            try:
                st.session_state.results_df = pd.read_csv("analysis_results.csv")
            except Exception as e:
                st.error(f"Error loading existing data: {e}")

    if 'is_capturing' not in st.session_state:
        st.session_state.is_capturing = False

    if 'captured_image_bytes' not in st.session_state:
        st.session_state.captured_image_bytes = None

    if 'latest_results' not in st.session_state:
        st.session_state.latest_results = None

    if 'focused_sample_index' not in st.session_state:
        st.session_state.focused_sample_index = 0

    # Function to get health status description
    def get_health_description(score, category):
        if category in ["nitrogenScore", "phosphorusScore", "potassiumScore",
                       "magnesiumScore", "sulfurScore", "calciumScore"]:
            if score >= 8:
                return "Excellent - No deficiency detected"
            elif score >= 6:
                return "Good - Minor deficiency"
            elif score >= 4:
                return "Fair - Moderate deficiency"
            else:
                return "Poor - Severe deficiency"
        elif category == "wiltingScore":
            if score >= 8:
                return "Excellent - No wilting detected"
            elif score >= 6:
                return "Good - Minor wilting"
            elif score >= 4:
                return "Fair - Moderate wilting"
            else:
                return "Poor - Severe wilting"
        return ""

    # Function to get recommendations based on scores
    def get_recommendations(results):
        recommendations = []
        nutrients = {
            "nitrogenScore": "nitrogen",
            "phosphorusScore": "phosphorus",
            "potassiumScore": "potassium",
            "magnesiumScore": "magnesium",
            "sulfurScore": "sulfur",
            "calciumScore": "calcium"
        }
        for score_key, nutrient in nutrients.items():
            score = results[score_key]
            if score < 4:
                recommendations.append(f"Apply {nutrient} fertilizer immediately - severe deficiency")
            elif score < 6:
                recommendations.append(f"Consider {nutrient} supplementation in the next irrigation")
        if results["wiltingScore"] < 4:
            recommendations.append("Increase irrigation immediately - plant showing severe water stress")
        elif results["wiltingScore"] < 6:
            recommendations.append("Monitor soil moisture and consider increasing irrigation frequency")
        damage_detected = results.get('damageDetected', False)
        damage_count = results.get('objectsDetectedCount', 0)
        if damage_detected:
            recommendations.append(f"Investigate pest activity - {damage_count if damage_count is not None else 'some'} potential damage areas detected")
            if damage_count is not None and damage_count > 10:
                recommendations.append("Consider applying appropriate pest control measures")
        if not recommendations:
            recommendations.append("Plants appear healthy. Continue current management practices.")
        return recommendations

    # Modified function to save to Firestore with userId
    def save_to_firestore(image_bytes, results):
        if db and st.session_state.user_id:
            try:
                now = datetime.now()
                timestamp_str = now.isoformat()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                image_type = "image/jpeg"  # Assuming JPEG from ESP32

                dominant_colors_firestore = []
                if results.get('dominantColors'):
                    for color in results['dominantColors']:
                        dominant_colors_firestore.append({"color": color})

                data = {
                    "userId": st.session_state.user_id,  # Add user ID to document
                    "userEmail": st.session_state.user_email,  # Add user email for reference
                    "imageData": image_base64,
                    "imageType": image_type,
                    "datetime": now,
                    "sampleId": results.get('sampleId'),
                    "sampleDate": results.get('sampleDate'),
                    "nitrogenScore": results.get('nitrogenScore'),
                    "phosphorusScore": results.get('phosphorusScore'),
                    "potassiumScore": results.get('potassiumScore'),
                    "magnesiumScore": results.get('magnesiumScore'),
                    "sulfurScore": results.get('sulfurScore'),
                    "calciumScore": results.get('calciumScore'),
                    "wiltingScore": results.get('wiltingScore'),
                    "objectsDetectedCount": results.get('objectsDetectedCount'),
                    "damageDetected": results.get('damageDetected'),
                    "dominantColors": dominant_colors_firestore,
                    "healthStatus": results.get('healthStatus'),
                    "damageSeverity": results.get('damageSeverity')
                }
                # Save under user-specific collection path
                db.collection("users").document(st.session_state.user_id).collection("maize_analysis").add(data)
                print(f"Data saved to Firestore for user {st.session_state.user_id}.")
            except Exception as e:
                st.error(f"Error saving to Firestore: {e}")
                st.error(f"Details: {e}")
        else:
            st.warning("Firestore not initialized or user not authenticated. Check credentials.")

    # Modified function to fetch data from Firestore by userId
    def fetch_maize_data():
        if db and st.session_state.user_id:
            try:
                # Query user-specific collection path
                docs = db.collection("users").document(st.session_state.user_id).collection("maize_analysis") \
                       .order_by("datetime", direction=firestore.Query.DESCENDING).get()
                data = [doc.to_dict() for doc in docs]
                for item in data:
                    if 'dominantColors' in item and isinstance(item['dominantColors'], list):
                        item['dominantColors_str'] = ", ".join([str(c['color']) for c in item['dominantColors']])
                        del item['dominantColors']  # Optionally remove the original list of dicts
                return pd.DataFrame(data)
            except Exception as e:
                st.error(f"Error fetching data from Firestore: {e}")
                return pd.DataFrame()
        else:
            st.warning("Firestore not initialized or user not authenticated. Check credentials.")
            return pd.DataFrame()

    def capture_and_analyze(esp32_camera_url):
        try:
            response = requests.get(esp32_camera_url, stream=True)
            response.raise_for_status()
            image_bytes = response.content
            st.session_state.captured_image_bytes = image_bytes

            # Save the captured image temporarily for analysis
            temp_path = "temp_continuous_capture.jpg"
            with open(temp_path, "wb") as f:
                f.write(image_bytes)

            analyzer = MaizeHealthAnalyzerImproved()
            results = analyzer.analyze_image(temp_path)
            
            # Add user ID and sample ID to results
            if 'sampleId' not in results or not results['sampleId']:
                # Generate a sample ID if not present
                results['sampleId'] = f"sample_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Add sample date if not present
            if 'sampleDate' not in results or not results['sampleDate']:
                results['sampleDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            st.session_state.latest_results = results

            # Save to Firestore
            save_to_firestore(image_bytes, results)

            # Add results to the local DataFrame and CSV
            new_row = pd.DataFrame([results])
            st.session_state.results_df = pd.concat([st.session_state.results_df, new_row], ignore_index=True)
            st.session_state.results_df.to_csv("analysis_results.csv", index=False)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            return Image.open(io.BytesIO(image_bytes)), results
        except requests.exceptions.RequestException as e:
            st.error(f"Error capturing image: {e}")
            return None, None
        except Exception as e:
            st.error(f"Error during analysis: {e}")
            return None, None

    # --- "Continuous Capture" Page ---
    if page == "Continuous Capture":
        st.header("Continuous Image Capture and Analysis")
        esp32_camera_url = st.text_input("Enter ESP32 Camera Capture URL:", "http://YOUR_ESP32_IP_ADDRESS/capture")
        capture_interval_minutes = st.number_input("Capture Interval (minutes)", min_value=0.1, step=0.1, value=0.1)
        capture_interval_seconds = capture_interval_minutes * 60

        col_display, col_results = st.columns(2)

        if not st.session_state.is_capturing:
            if st.button("Start Continuous Capture"):
                st.session_state.is_capturing = True
                st.info(f"Continuous capture started. Data will be saved to Firestore every {capture_interval_minutes} minutes.")

        if st.session_state.is_capturing:
            stop_button = st.button("Stop Continuous Capture")
            if stop_button:
                st.session_state.is_capturing = False
                st.info("Continuous capture stopped.")

            if st.session_state.is_capturing:
                with st.spinner(f"Capturing and analyzing every {capture_interval_minutes} minutes..."):
                    image, results = capture_and_analyze(esp32_camera_url)
                    if image:
                        with col_display:
                            st.subheader("Live Feed")
                            st.image(image, width=400)
                        if results:
                            with col_results:
                                st.subheader("Latest Analysis")
                                st.metric("Wilting Score", f"{results['wiltingScore']}/10", delta=f"{'Good' if results['wiltingScore'] >= 6 else 'Needs attention'}")
                                damage_detected = results.get('damageDetected', False)
                                damage_count = results.get('objectsDetectedCount', 0)
                                st.metric("Damage Detected", "Yes" if damage_detected else "No", delta=f"{damage_count} areas" if damage_detected else "None")
                                nutrient_cols = st.columns(3)
                                nutrients = {"N": "nitrogenScore", "P": "phosphorusScore", "K": "potassiumScore", "Mg": "magnesiumScore", "S": "sulfurScore", "Ca": "calciumScore"}
                                i = 0
                                for label, key in nutrients.items():
                                    with nutrient_cols[i % 3]:
                                        score = results.get(key, 0)
                                        st.metric(label, f"{score}/10", delta=f"{'Good' if score >= 6 else 'Needs attention'}")
                                    i += 1
                                st.subheader("Recommendations")
                                for rec in get_recommendations(results):
                                    st.info(rec)
                    time.sleep(capture_interval_seconds)
                    st.rerun()  # Rerun to trigger the next capture

    # --- "Upload & Analyze" Page ---
    elif page == "Upload & Analyze":
        st.header("Upload Images for Analysis")
        uploaded_file = st.file_uploader("Choose a maize image", type=["jpg", "jpeg", "png"])
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Uploaded Image")
                image = Image.open(uploaded_file)
                st.image(image, width=400)
            
            # Allow user to provide a sample ID
            sample_id = st.text_input("Sample ID (optional)", value=f"sample_{datetime.now().strftime('%Y%m%d%H%M%S')}")
            
            temp_path = "temp_upload.jpg"
            image_bytes = uploaded_file.getvalue()
            with open(temp_path, "wb") as f:
                f.write(image_bytes)
            with st.spinner("Analyzing image..."):
                analyzer = MaizeHealthAnalyzerImproved()
                results = analyzer.analyze_image(temp_path)
                
                # Add user-provided sample ID and current date
                results['sampleId'] = sample_id
                results['sampleDate'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                analyzer.visualize_results("temp_result.png")

                # Save to Firestore
                save_to_firestore(image_bytes, results)

            with col2:
                st.subheader("Analysis Visualization")
                st.image("temp_result.png", width=400)
            st.header("Analysis Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("Nutrient Status")
                nutrients = {
                    "Nitrogen": results["nitrogenScore"],
                    "Phosphorus": results["phosphorusScore"],
                    "Potassium": results["potassiumScore"],
                    "Magnesium": results["magnesiumScore"],
                    "Sulfur": results["sulfurScore"],
                    "Calcium": results["calciumScore"]
                }
                for nutrient, score in nutrients.items():
                    st.metric(
                        label=nutrient,
                        value=f"{score}/10",
                        delta=f"{'Good' if score >= 6 else 'Needs attention'}"
                    )
            with col2:
                st.subheader("Water Stress")
                st.metric(
                    label="Wilting Score",
                    value=f"{results['wiltingScore']}/10",
                    delta=f"{'Good' if results['wiltingScore'] >= 6 else 'Needs attention'}"
                )
                st.subheader("Pest/Disease")
                damage_detected = results.get('damageDetected', False)
                damage_count = results.get('objectsDetectedCount', 0)
                st.metric(
                    label="Damage Detected",
                    value="Yes" if damage_detected else "No",
                    delta=f"{damage_count} areas" if damage_detected else "None"
                )
            with col3:
                st.subheader("Recommendations")
                recommendations = get_recommendations(results)
                for rec in recommendations:
                    st.info(rec)
            new_row = pd.DataFrame([results])
            st.session_state.results_df = pd.concat([st.session_state.results_df, new_row], ignore_index=True)
            st.session_state.results_df.to_csv("analysis_results.csv", index=False)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists("temp_result.png"):
                os.remove("temp_result.png")

    # --- "View Results" Page ---
    elif page == "View Results":
        st.header("View Analysis Results")
        firestore_df = fetch_maize_data()

        if firestore_df.empty:
            st.info("No analysis results available in Firestore yet.")
        else:
            def set_focused_sample(index):
                st.session_state.focused_sample_index = index

            st.subheader("Focused Sample")
            focused_sample = firestore_df.iloc[st.session_state.focused_sample_index]

            col_focused_1, col_focused_2 = st.columns(2)

            with col_focused_1:
                if focused_sample.get('imageData'):
                    try:
                        image_bytes = base64.b64decode(focused_sample['imageData'])
                        image = Image.open(io.BytesIO(image_bytes))
                        st.image(image, caption="Captured Image", width=400)
                    except Exception as e:
                        st.error(f"Error displaying image: {e}")

                st.subheader("Sample Information")
                timestamp = focused_sample.get('datetime')
                sample_date_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
                st.write(f"Sample ID: {focused_sample.get('sampleId', 'N/A')}")
                st.write(f"Sample Date: {sample_date_str}")

                st.subheader("Health Summary")
                overall_health = focused_sample.get('healthStatus', "Unknown")
                st.write(f"Overall Health: {overall_health}")
                st.write(f"Water Stress: {get_health_description(focused_sample.get('wiltingScore', 5), 'wiltingScore')}")
                damage_status = "Detected" if focused_sample.get('damageDetected', False) else "None detected"
                st.write(f"Pest/Disease Damage: {damage_status}")
                if focused_sample.get('damageDetected', False):
                    st.write(f"Potential damage areas: {focused_sample.get('objectsDetectedCount', 0)}")

                st.subheader("Recommendations")
                recommendations = get_recommendations({
                    "nitrogenScore": focused_sample.get('nitrogenScore', 5),
                    "phosphorusScore": focused_sample.get('phosphorusScore', 5),
                    "potassiumScore": focused_sample.get('potassiumScore', 5),
                    "magnesiumScore": focused_sample.get('magnesiumScore', 5),
                    "sulfurScore": focused_sample.get('sulfurScore', 5),
                    "calciumScore": focused_sample.get('calciumScore', 5),
                    "wiltingScore": focused_sample.get('wiltingScore', 5),
                    "damageDetected": focused_sample.get('damageDetected', False),
                    "objectsDetectedCount": focused_sample.get('objectsDetectedCount', 0)
                })
                for rec in recommendations:
                    st.info(rec)

            with col_focused_2:
                st.subheader("Nutrient Scores")
                labels = ['Nitrogen', 'Phosphorus', 'Potassium', 'Magnesium', 'Sulfur', 'Calcium']
                scores = [
                    focused_sample.get('nitrogenScore', 5),
                    focused_sample.get('phosphorusScore', 5),
                    focused_sample.get('potassiumScore', 5),
                    focused_sample.get('magnesiumScore', 5),
                    focused_sample.get('sulfurScore', 5),
                    focused_sample.get('calciumScore', 5)
                ]
                angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
                scores.append(scores[0])
                angles.append(angles[0])
                fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                ax.plot(angles, scores, 'o-', linewidth=2)
                ax.fill(angles, scores, alpha=0.25)
                ax.set_thetagrids(np.degrees(angles[:-1]), labels)
                ax.set_ylim(0, 10)
                ax.set_title("Nutrient Scores")
                ax.grid(True)
                buf = io.BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)
                st.image(buf)

            st.subheader("All Analysis Results")

            def handle_focus_click(row):
                st.session_state.focused_sample_index = row.name

            edited_df = st.data_editor(
                firestore_df.assign(Focus=False),  # Add a Focus column
                column_config={
                    "Focus": st.column_config.CheckboxColumn(
                        "Focus on this sample",
                        default=False,
                    )
                },
                hide_index=True,
                key="results_table"
            )

            # Get the index of the first row where 'Focus' is True
            focused_row = edited_df[edited_df['Focus']]
            if not focused_row.empty:
                st.session_state.focused_sample_index = focused_row.index[0]
                # Reset the 'Focus' column to False after selection (optional)
                edited_df['Focus'] = False
                # Update the data editor
                st.session_state["results_table_data"] = edited_df.to_dict('records')
                st.rerun()  # Rerun to update the focused sample display

    # --- "Historical Data" Page ---
    elif page == "Historical Data":
        st.header("Historical Data Analysis")
        firestore_df = fetch_maize_data()

        if firestore_df.empty:
            st.info("No historical data available in Firestore yet.")
        else:
            # Ensure 'datetime' column is in datetime format for plotting
            if 'datetime' in firestore_df.columns:
                firestore_df['datetime'] = pd.to_datetime(firestore_df['datetime'])
                date_column_available = True
            else:
                date_column_available = False

            st.subheader("Nutrient Trends Over Time")
            if date_column_available:
                grouped_df = firestore_df.set_index('datetime').resample('D').mean(numeric_only=True)
                fig, ax = plt.subplots(figsize=(10, 6))
                nutrients = ['nitrogenScore', 'phosphorusScore', 'potassiumScore', 'magnesiumScore', 'sulfurScore', 'calciumScore']
                for nutrient in nutrients:
                    if nutrient in grouped_df.columns:
                        ax.plot(grouped_df.index, grouped_df[nutrient], marker='o', label=nutrient.replace('Score', ''))
                ax.set_xlabel('Date')
                ax.set_ylabel('Score (1-10)')
                ax.set_title('Nutrient Scores Over Time')
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)

                if 'wiltingScore' in grouped_df.columns:
                    st.subheader("Water Stress Trend Over Time")
                    fig2, ax2 = plt.subplots(figsize=(10, 4))
                    ax2.plot(grouped_df.index, grouped_df['wiltingScore'], marker='o', color='blue')
                    ax2.set_xlabel('Date')
                    ax2.set_ylabel('Wilting Score (1-10)')
                    ax2.set_title('Wilting Score Over Time')
                    ax2.grid(True)
                    st.pyplot(fig2)

                if 'damageDetected' in firestore_df.columns and date_column_available:
                    damage_incidence = firestore_df.set_index('datetime').resample('D')['damageDetected'].sum()
                    fig3, ax3 = plt.subplots(figsize=(10, 4))
                    ax3.plot(damage_incidence.index, damage_incidence.values, marker='o', color='red')
                    ax3.set_xlabel('Date')
                    ax3.set_ylabel('Number of Samples with Damage')
                    ax3.set_title('Pest/Disease Incidence Over Time')
                    ax3.grid(True)
                    st.pyplot(fig3)
            else:
                st.warning("Datetime information not available for trend analysis.")

            # Add filtering options
            st.subheader("Data Filtering")
            date_range = st.date_input(
                "Filter by date range",
                [
                    firestore_df['datetime'].min().date() if not firestore_df.empty and date_column_available else datetime.now().date(),
                    firestore_df['datetime'].max().date() if not firestore_df.empty and date_column_available else datetime.now().date()
                ]
            )
            
            # Filter data by date range if available
            if date_column_available and len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = firestore_df[
                    (firestore_df['datetime'].dt.date >= start_date) & 
                    (firestore_df['datetime'].dt.date <= end_date)
                ]
            else:
                filtered_df = firestore_df
            
            st.subheader("Filtered Data")
            st.dataframe(filtered_df)

# Main application flow
if st.session_state.user_authenticated:
    show_main_application()
else:
    show_login_page()