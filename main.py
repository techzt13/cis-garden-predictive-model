#!/usr/bin/env python3
"""
Interactive Harvest Forecasting Tool - CISHK Garden
Terminal-based interface for harvest predictions
"""

import sys
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from forecast_engine import HarvestForecaster
from vegetable_database import PLANT_DATA


def search_plants(query):
    """
    Search for plants matching the query
    
    Args:
        query: Search string
    
    Returns:
        List of matching plant names
    """
    if not query or query.strip() == "":
        # Return all plants
        return sorted(PLANT_DATA.keys())
    
    query_lower = query.lower()
    matches = [
        plant for plant in PLANT_DATA.keys()
        if query_lower in plant.lower()
    ]
    
    return sorted(matches)


def display_plant_list(plants, query=""):
    """
    Display list of plants with indices
    
    Args:
        plants: List of plant names
        query: Search query (for display)
    """
    if len(plants) == 0:
        print(f"\n❌ No plants found matching '{query}'")
        return
    
    print(f"\n📋 Found {len(plants)} plant(s):")
    print("=" * 70)
    
    for idx, plant in enumerate(plants, 1):
        plant_info = PLANT_DATA[plant]
        print(f"{idx:3d}. {plant:45s} (GDD: {plant_info['target_gdd']:4d}, Base: {plant_info['base_temp']:2d}°C)")
    
    print("=" * 70)


def get_user_selection(plants):
    """
    Get user's plant selection
    
    Args:
        plants: List of available plants
    
    Returns:
        Selected plant name or None
    """
    while True:
        try:
            selection = input(f"\nSelect plant [1-{len(plants)}] or 'q' to quit: ").strip()
            
            if selection.lower() == 'q':
                return None
            
            idx = int(selection)
            if 1 <= idx <= len(plants):
                return plants[idx - 1]
            else:
                print(f"❌ Please enter a number between 1 and {len(plants)}")
        
        except ValueError:
            print("❌ Please enter a valid number or 'q' to quit")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return None


def get_planting_date():
    """
    Get planting date from user
    
    Returns:
        datetime object or None
    """
    while True:
        try:
            date_str = input("\n📅 Date Planted (YYYY-MM-DD): ").strip()
            
            if date_str.lower() == 'q':
                return None
            
            planting_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Validate date is not too far in the future
            if planting_date > datetime.now():
                print("⚠️  Warning: Planting date is in the future")
                confirm = input("Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            # Validate date is not too far in the past
            if planting_date < datetime(2015, 1, 1):
                print("❌ Planting date is too far in the past (before 2015)")
                continue
            
            return planting_date
        
        except ValueError:
            print("❌ Invalid date format. Please use YYYY-MM-DD (e.g., 2026-01-15)")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            return None


def create_forecast_chart(prediction, output_file="harvest_forecast.png"):
    """
    Create and save a harvest forecast visualization
    
    Args:
        prediction: Prediction dictionary from forecaster
        output_file: Output filename
    """
    try:
        # Extract GDD timeline data
        timeline = prediction.get('gdd_timeline', [])
        if not timeline:
            print("⚠️  No timeline data available for chart")
            return
        
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
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n📊 Chart saved: {output_file}")
        
    except Exception as e:
        print(f"⚠️  Error creating chart: {e}")


def display_prediction(prediction):
    """
    Display prediction results
    
    Args:
        prediction: Prediction dictionary
    """
    print("\n" + "=" * 70)
    print("🌱 HARVEST FORECAST RESULTS")
    print("=" * 70)
    
    if "error" in prediction:
        print(f"\n❌ Error: {prediction['error']}")
        return
    
    print(f"\n🌿 Selected: {prediction['plant_name']}")
    print(f"🎯 Target GDD: {prediction['target_gdd']}")
    print(f"🌡️  Base Temperature: {prediction['base_temp']}°C")
    print(f"📅 Planted: {prediction['planting_date']}")
    
    # Current status
    print(f"\n📊 Current Status:")
    print(f"   Accumulated GDD: {prediction['current_gdd']:.1f}")
    progress = (prediction['current_gdd'] / prediction['target_gdd']) * 100
    print(f"   Progress: {progress:.1f}%")
    
    # Progress bar
    bar_length = 40
    filled = int(bar_length * progress / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"   [{bar}]")
    
    # Harvest prediction
    print(f"\n🎉 Forecast:")
    print(f"   Harvest Ready: {prediction['harvest_date']}")
    print(f"   Days from Planting: {prediction['days_to_harvest']}")
    
    if 'uncertainty_days' in prediction:
        print(f"   Uncertainty Range: ±{prediction['uncertainty_days']} days")
    
    print(f"   Confidence: {prediction['confidence']}")
    
    if 'note' in prediction:
        print(f"   Note: {prediction['note']}")
    
    print("\n" + "=" * 70)


def main():
    """
    Main interactive loop
    """
    print("\n" + "=" * 70)
    print(" 🌱 INTERACTIVE HARVEST FORECASTING ENGINE 🌱")
    print(" Chinese International School Hong Kong (CISHK) Garden")
    print(" Location: 22.2855°N, 114.1989°E")
    print("=" * 70)
    
    # Initialize forecaster
    print("\n🔄 Initializing forecaster...")
    forecaster = HarvestForecaster(latitude=22.2855, longitude=114.1989)
    
    # Main loop
    while True:
        print("\n" + "-" * 70)
        
        # Search for plants
        query = input("\n🔍 Enter plant name to search (or press Enter to see all): ").strip()
        
        matches = search_plants(query)
        
        if len(matches) == 0:
            print(f"\n❌ No plants found matching '{query}'")
            retry = input("Try another search? (y/n): ").strip().lower()
            if retry != 'y':
                break
            continue
        
        # Display matches
        display_plant_list(matches, query)
        
        # Get selection
        selected_plant = get_user_selection(matches)
        
        if selected_plant is None:
            print("\n👋 Exiting... Happy gardening!")
            break
        
        # Get planting date
        planting_date = get_planting_date()
        
        if planting_date is None:
            print("\n👋 Exiting... Happy gardening!")
            break
        
        # Make prediction
        print("\n🔄 Calculating harvest forecast...")
        print("   • Fetching NASA POWER historical data (2015-present)...")
        print("   • Fetching Open-Meteo 7-day forecast...")
        print("   • Computing Growing Degree Days...")
        
        prediction = forecaster.predict_harvest_date(selected_plant, planting_date)
        
        # Display results
        display_prediction(prediction)
        
        # Create visualization
        if "error" not in prediction:
            print("\n🎨 Generating forecast chart...")
            create_forecast_chart(prediction)
        
        # Ask if user wants to continue
        print("\n" + "-" * 70)
        another = input("\n🔄 Forecast another plant? (y/n): ").strip().lower()
        
        if another != 'y':
            print("\n👋 Thank you for using the Harvest Forecaster!")
            print("   Happy gardening! 🌱🌿🍅")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
