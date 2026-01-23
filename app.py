"""
CISHK Garden Harvest Forecaster - Web Application
Streamlit-based interactive web interface for harvest predictions
"""

import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from vegetable_database import PLANT_DATA
from forecast_engine import HarvestForecaster


# Page configuration
st.set_page_config(
    page_title="CISHK Garden Harvest Forecaster",
    page_icon="🥬",
    layout="wide",
    initial_sidebar_state="expanded"
)


def create_forecast_chart(prediction):
    """
    Create a harvest forecast visualization for Streamlit
    
    Args:
        prediction: Prediction dictionary from forecaster
        
    Returns:
        matplotlib figure object
    """
    # Extract GDD timeline data
    timeline = prediction.get('gdd_timeline', [])
    if not timeline:
        return None
    
    # Prepare data for plotting
    dates = [datetime.strptime(str(record['date']), "%Y-%m-%d %H:%M:%S") if isinstance(record['date'], str) else record['date'] for record in timeline]
    daily_gdd = [record['gdd'] for record in timeline]
    cumulative_gdd = [record['cumulative_gdd'] for record in timeline]
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle(f"Harvest Forecast: {prediction['plant_name']}", fontsize=16, fontweight='bold')
    
    # Plot 1: Daily GDD
    ax1.bar(dates, daily_gdd, color='skyblue', alpha=0.7, edgecolor='navy')
    ax1.set_ylabel('Daily GDD', fontsize=12, fontweight='bold')
    ax1.set_title('Daily Growing Degree Days', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.tick_params(axis='x', rotation=45)
    
    # Plot 2: Cumulative GDD
    ax2.plot(dates, cumulative_gdd, color='green', linewidth=2, label='Accumulated GDD')
    ax2.axhline(y=prediction['target_gdd'], color='red', linestyle='--', linewidth=2, label=f"Target ({prediction['target_gdd']} GDD)")
    
    # Mark harvest date
    harvest_date = datetime.strptime(prediction['harvest_date'], "%Y-%m-%d")
    ax2.axvline(x=harvest_date, color='orange', linestyle='--', linewidth=2, label=f"Harvest: {prediction['harvest_date']}")
    
    # Mark current date
    current_date = datetime.now()
    if current_date >= dates[0] and current_date <= dates[-1]:
        ax2.axvline(x=current_date, color='purple', linestyle=':', linewidth=2, label='Today')
    
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative GDD', fontsize=12, fontweight='bold')
    ax2.set_title('Growing Degree Day Accumulation', fontsize=12)
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.tick_params(axis='x', rotation=45)
    
    # Add info text
    info_text = f"Planted: {prediction['planting_date']} | Target: {prediction['target_gdd']} GDD | Base Temp: {prediction['base_temp']}°C"
    fig.text(0.5, 0.02, info_text, ha='center', fontsize=10, style='italic')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    return fig


def main():
    """
    Main Streamlit application
    """
    # Header
    st.title("🌱 CISHK Garden Harvest Forecaster 🥬")
    st.markdown("### Chinese International School Hong Kong")
    st.markdown("**Location:** 22.2855°N, 114.1989°E | **Database:** 512+ plant varieties")
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("📖 About")
        st.info(
            """
            This tool predicts harvest dates using **Growing Degree Days (GDD)** methodology.
            
            **How it works:**
            - Fetches historical weather data from NASA POWER API (2015-present)
            - Uses Open-Meteo for 7-day forecast
            - Calculates GDD accumulation from planting date
            - Predicts harvest based on plant-specific GDD requirements
            """
        )
        
        st.header("🌡️ GDD Formula")
        st.latex(r"GDD = \frac{T_{max} + T_{min}}{2} - T_{base}")
        
        st.header("📊 Database Stats")
        st.metric("Total Plants", len(PLANT_DATA))
        
        # Show variety breakdown
        categories = {}
        for plant_name in PLANT_DATA.keys():
            category = plant_name.split("(")[0].strip()
            categories[category] = categories.get(category, 0) + 1
        
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        st.markdown("**Top 5 Categories:**")
        for cat, count in top_categories:
            st.markdown(f"- {cat}: {count} varieties")
    
    # Main content - two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("🔍 Select Your Plant")
        
        # Search box
        search_query = st.text_input("🔎 Search plants:", placeholder="e.g., Tomato, Bok Choy, Lettuce")
        
        # Filter plants based on search
        if search_query:
            filtered_plants = [p for p in PLANT_DATA.keys() if search_query.lower() in p.lower()]
        else:
            filtered_plants = sorted(PLANT_DATA.keys())
        
        st.info(f"Showing {len(filtered_plants)} plant(s)")
        
        # Plant selection
        selected_plant = st.selectbox(
            "Choose a plant variety:",
            options=filtered_plants,
            format_func=lambda x: f"{x} (GDD: {PLANT_DATA[x]['target_gdd']}, Base: {PLANT_DATA[x]['base_temp']}°C)"
        )
        
        if selected_plant:
            plant_info = PLANT_DATA[selected_plant]
            
            # Display plant details
            st.markdown("#### 📋 Plant Details")
            metric_col1, metric_col2 = st.columns(2)
            with metric_col1:
                st.metric("Target GDD", plant_info['target_gdd'])
            with metric_col2:
                st.metric("Base Temperature", f"{plant_info['base_temp']}°C")
    
    with col2:
        st.header("📅 Planting Information")
        
        # Date input
        planting_date = st.date_input(
            "When did you plant?",
            value=datetime.now() - timedelta(days=30),
            min_value=datetime(2015, 1, 1),
            max_value=datetime.now() + timedelta(days=365)
        )
        
        st.markdown(f"**Selected date:** {planting_date.strftime('%Y-%m-%d')}")
        
        # Predict button
        predict_button = st.button("🎯 Predict Harvest Date", type="primary", use_container_width=True)
    
    # Prediction section
    if predict_button and selected_plant:
        st.markdown("---")
        st.header("🎉 Harvest Forecast Results")
        
        with st.spinner("🔄 Calculating harvest forecast..."):
            # Initialize forecaster
            forecaster = HarvestForecaster(latitude=22.2855, longitude=114.1989)
            
            # Make prediction
            prediction = forecaster.predict_harvest_date(selected_plant, planting_date.strftime("%Y-%m-%d"))
        
        if "error" in prediction:
            st.error(f"❌ Error: {prediction['error']}")
        else:
            # Display results in columns
            result_col1, result_col2, result_col3 = st.columns(3)
            
            with result_col1:
                st.metric(
                    "🗓️ Harvest Date",
                    prediction['harvest_date'],
                    delta=f"{prediction['days_to_harvest']} days from planting"
                )
            
            with result_col2:
                progress_pct = (prediction['current_gdd'] / prediction['target_gdd']) * 100
                st.metric(
                    "📊 Current Progress",
                    f"{progress_pct:.1f}%",
                    delta=f"{prediction['current_gdd']:.0f} / {prediction['target_gdd']} GDD"
                )
            
            with result_col3:
                # Calculate days remaining
                harvest_date = datetime.strptime(prediction['harvest_date'], "%Y-%m-%d")
                days_remaining = (harvest_date - datetime.now()).days
                
                if days_remaining > 0:
                    st.metric(
                        "⏳ Days Remaining",
                        days_remaining,
                        delta="Until harvest"
                    )
                else:
                    st.success("✅ Ready to Harvest!")
                    st.metric("Days Since Harvest Date", abs(days_remaining))
            
            # Progress bar
            progress = min(progress_pct / 100, 1.0)
            st.progress(progress)
            
            # Confidence badge
            if prediction['confidence'] == 'HIGH':
                st.success(f"🎯 Confidence Level: **{prediction['confidence']}** (Based on actual weather data)")
            else:
                st.warning(f"⚠️ Confidence Level: **{prediction['confidence']}** (Includes projected data)")
            
            if 'note' in prediction:
                st.info(f"ℹ️ {prediction['note']}")
            
            # Display chart
            st.markdown("---")
            st.header("📈 GDD Accumulation Chart")
            
            fig = create_forecast_chart(prediction)
            if fig:
                st.pyplot(fig)
            else:
                st.warning("No chart data available")
            
            # Additional details in expander
            with st.expander("📊 View Detailed Timeline Data"):
                import pandas as pd
                
                timeline_df = pd.DataFrame(prediction['gdd_timeline'])
                timeline_df['date'] = pd.to_datetime(timeline_df['date'])
                timeline_df = timeline_df.rename(columns={
                    'date': 'Date',
                    'gdd': 'Daily GDD',
                    'cumulative_gdd': 'Cumulative GDD'
                })
                
                # Show last 30 days or all available
                display_rows = min(30, len(timeline_df))
                st.dataframe(
                    timeline_df.tail(display_rows).style.format({
                        'Daily GDD': '{:.1f}',
                        'Cumulative GDD': '{:.1f}'
                    }),
                    use_container_width=True
                )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
            <p>🌱 CISHK Garden Harvest Forecaster | Powered by NASA POWER & Open-Meteo APIs</p>
            <p>Data sources: Historical weather (2015-present) + 7-day forecast</p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
