"""
Harvest Forecast Engine for CISHK Garden
Fetches real-time weather data and calculates GDD-based harvest predictions
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from vegetable_database import PLANT_DATA


class HarvestForecaster:
    """
    Calculates harvest dates using Growing Degree Days (GDD) methodology
    Combines historical NASA POWER data with Open-Meteo forecast
    """
    
    def __init__(self, latitude=22.2855, longitude=114.1989):
        """
        Initialize forecaster for CISHK location
        
        Args:
            latitude: Garden latitude (default: CISHK)
            longitude: Garden longitude (default: CISHK)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.historical_data = None
        self.forecast_data = None
        
    def fetch_nasa_power_data(self, start_date="2015-01-01", end_date=None):
        """
        Fetch historical weather data from NASA POWER API
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (default: today)
        
        Returns:
            pandas DataFrame with daily temperature data
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        print(f"Fetching NASA POWER historical data ({start_date} to {end_date})...")
        
        # NASA POWER API endpoint
        base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        
        params = {
            "parameters": "T2M_MAX,T2M_MIN",
            "community": "AG",
            "longitude": self.longitude,
            "latitude": self.latitude,
            "start": start_date.replace("-", ""),
            "end": end_date.replace("-", ""),
            "format": "JSON"
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Extract temperature data
            t_max = data['properties']['parameter']['T2M_MAX']
            t_min = data['properties']['parameter']['T2M_MIN']
            
            # Convert to DataFrame
            dates = pd.to_datetime(list(t_max.keys()), format='%Y%m%d')
            df = pd.DataFrame({
                'date': dates,
                'temp_max': list(t_max.values()),
                'temp_min': list(t_min.values())
            })
            
            # Clean data: Remove NASA's -999 error values
            df = df[(df['temp_max'] > -100) & (df['temp_min'] > -100)]
            
            # Reset index
            df = df.reset_index(drop=True)
            
            print(f"✓ Retrieved {len(df)} days of historical data")
            self.historical_data = df
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching NASA POWER data: {e}")
            return None
    
    def fetch_open_meteo_forecast(self):
        """
        Fetch 7-day weather forecast from Open-Meteo API
        
        Returns:
            pandas DataFrame with forecast temperature data
        """
        print("Fetching 7-day forecast from Open-Meteo...")
        
        # Open-Meteo API endpoint
        base_url = "https://api.open-meteo.com/v1/forecast"
        
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto"
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extract forecast data
            daily = data['daily']
            df = pd.DataFrame({
                'date': pd.to_datetime(daily['time']),
                'temp_max': daily['temperature_2m_max'],
                'temp_min': daily['temperature_2m_min']
            })
            
            print(f"✓ Retrieved {len(df)} days of forecast data")
            self.forecast_data = df
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Open-Meteo forecast: {e}")
            return None
    
    def calculate_gdd(self, temp_max, temp_min, base_temp):
        """
        Calculate Growing Degree Days for a single day
        
        Formula: GDD = ((T_max + T_min) / 2) - T_base
        Negative values are set to 0
        
        Args:
            temp_max: Maximum daily temperature (°C)
            temp_min: Minimum daily temperature (°C)
            base_temp: Base temperature for crop (°C)
        
        Returns:
            GDD value for the day
        """
        avg_temp = (temp_max + temp_min) / 2
        gdd = avg_temp - base_temp
        return max(0, gdd)  # GDD cannot be negative
    
    def get_historical_gdd_rate(self, base_temp, years=10):
        """
        Calculate average daily GDD accumulation rate from historical data
        
        Args:
            base_temp: Base temperature for the crop
            years: Number of years to analyze
        
        Returns:
            Average daily GDD rate
        """
        if self.historical_data is None:
            self.fetch_nasa_power_data()
        
        # Filter to last N years
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        df = self.historical_data[self.historical_data['date'] >= start_date].copy()
        
        # Calculate GDD for each day
        df['gdd'] = df.apply(
            lambda row: self.calculate_gdd(row['temp_max'], row['temp_min'], base_temp),
            axis=1
        )
        
        # Average daily GDD
        avg_daily_gdd = df['gdd'].mean()
        
        return avg_daily_gdd
    
    def predict_harvest_date(self, plant_name, planting_date):
        """
        Predict harvest date based on GDD accumulation
        
        Args:
            plant_name: Name of plant from database
            planting_date: Date planted (datetime object or YYYY-MM-DD string)
        
        Returns:
            dict with prediction details
        """
        # Validate plant
        if plant_name not in PLANT_DATA:
            return {"error": f"Plant '{plant_name}' not found in database"}
        
        plant_info = PLANT_DATA[plant_name]
        base_temp = plant_info['base_temp']
        target_gdd = plant_info['target_gdd']
        
        # Convert planting date to datetime
        if isinstance(planting_date, str):
            planting_date = datetime.strptime(planting_date, "%Y-%m-%d")
        
        # Fetch data if not already loaded
        if self.historical_data is None:
            self.fetch_nasa_power_data()
        
        if self.forecast_data is None:
            self.fetch_open_meteo_forecast()
        
        # Combine historical and forecast data
        all_data = pd.concat([self.historical_data, self.forecast_data], ignore_index=True)
        all_data = all_data.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
        
        # Filter data from planting date onward
        df = all_data[all_data['date'] >= pd.Timestamp(planting_date)].copy()
        
        if len(df) == 0:
            return {"error": "Planting date is in the future beyond forecast range"}
        
        # Calculate GDD for each day
        df['gdd'] = df.apply(
            lambda row: self.calculate_gdd(row['temp_max'], row['temp_min'], base_temp),
            axis=1
        )
        
        # Calculate cumulative GDD
        df['cumulative_gdd'] = df['gdd'].cumsum()
        
        # Find when target GDD is reached
        harvest_rows = df[df['cumulative_gdd'] >= target_gdd]
        
        if len(harvest_rows) > 0:
            # Target reached within available data
            harvest_date = harvest_rows.iloc[0]['date']
            current_gdd = df.iloc[-1]['cumulative_gdd'] if pd.Timestamp(datetime.now()) >= df.iloc[-1]['date'] else df[df['date'] <= pd.Timestamp(datetime.now())]['cumulative_gdd'].iloc[-1] if len(df[df['date'] <= pd.Timestamp(datetime.now())]) > 0 else 0
            days_to_harvest = (harvest_date - planting_date).days
            
            result = {
                "plant_name": plant_name,
                "base_temp": base_temp,
                "target_gdd": target_gdd,
                "planting_date": planting_date.strftime("%Y-%m-%d"),
                "current_gdd": round(current_gdd, 1),
                "harvest_date": harvest_date.strftime("%Y-%m-%d"),
                "days_to_harvest": days_to_harvest,
                "confidence": "HIGH",
                "gdd_timeline": df[['date', 'gdd', 'cumulative_gdd']].to_dict('records')
            }
            
        else:
            # Target not yet reached - need to project
            current_gdd = df['cumulative_gdd'].iloc[-1]
            remaining_gdd = target_gdd - current_gdd
            
            # Calculate average daily GDD rate from historical data
            avg_daily_gdd = self.get_historical_gdd_rate(base_temp, years=10)
            
            # Estimate remaining days
            if avg_daily_gdd > 0:
                remaining_days = int(np.ceil(remaining_gdd / avg_daily_gdd))
                last_date = df['date'].iloc[-1]
                estimated_harvest = last_date + timedelta(days=remaining_days)
                
                # Calculate uncertainty (±10% of remaining time)
                uncertainty_days = max(1, int(remaining_days * 0.1))
                
                result = {
                    "plant_name": plant_name,
                    "base_temp": base_temp,
                    "target_gdd": target_gdd,
                    "planting_date": planting_date.strftime("%Y-%m-%d"),
                    "current_gdd": round(current_gdd, 1),
                    "harvest_date": estimated_harvest.strftime("%Y-%m-%d"),
                    "days_to_harvest": (estimated_harvest - planting_date).days,
                    "confidence": "MEDIUM",
                    "uncertainty_days": uncertainty_days,
                    "note": f"Projected using {avg_daily_gdd:.1f} GDD/day average",
                    "gdd_timeline": df[['date', 'gdd', 'cumulative_gdd']].to_dict('records')
                }
            else:
                result = {
                    "error": "Cannot calculate harvest date - insufficient GDD accumulation rate"
                }
        
        return result
    
    def get_current_status(self, plant_name, planting_date):
        """
        Get current growing status without full prediction
        
        Args:
            plant_name: Name of plant from database
            planting_date: Date planted (datetime object or YYYY-MM-DD string)
        
        Returns:
            dict with current GDD accumulation
        """
        if plant_name not in PLANT_DATA:
            return {"error": f"Plant '{plant_name}' not found in database"}
        
        plant_info = PLANT_DATA[plant_name]
        base_temp = plant_info['base_temp']
        target_gdd = plant_info['target_gdd']
        
        if isinstance(planting_date, str):
            planting_date = datetime.strptime(planting_date, "%Y-%m-%d")
        
        if self.historical_data is None:
            self.fetch_nasa_power_data()
        
        # Get data from planting to today
        today = datetime.now()
        df = self.historical_data[
            (self.historical_data['date'] >= pd.Timestamp(planting_date)) &
            (self.historical_data['date'] <= pd.Timestamp(today))
        ].copy()
        
        if len(df) == 0:
            return {"current_gdd": 0, "target_gdd": target_gdd, "progress": 0}
        
        # Calculate GDD
        df['gdd'] = df.apply(
            lambda row: self.calculate_gdd(row['temp_max'], row['temp_min'], base_temp),
            axis=1
        )
        
        current_gdd = df['gdd'].sum()
        progress = (current_gdd / target_gdd) * 100
        
        return {
            "current_gdd": round(current_gdd, 1),
            "target_gdd": target_gdd,
            "progress": round(progress, 1),
            "days_elapsed": len(df)
        }


if __name__ == "__main__":
    # Test the forecaster
    print("=" * 60)
    print("HARVEST FORECASTER - CISHK GARDEN")
    print("=" * 60)
    
    forecaster = HarvestForecaster()
    
    # Test with a sample plant
    test_plant = "Tomato (Cherry)"
    test_date = "2026-01-01"
    
    print(f"\nTesting with: {test_plant}")
    print(f"Planted: {test_date}\n")
    
    prediction = forecaster.predict_harvest_date(test_plant, test_date)
    
    if "error" not in prediction:
        print(f"Plant: {prediction['plant_name']}")
        print(f"Target GDD: {prediction['target_gdd']}")
        print(f"Current GDD: {prediction['current_gdd']}")
        print(f"Estimated Harvest: {prediction['harvest_date']}")
        print(f"Days to Harvest: {prediction['days_to_harvest']}")
        print(f"Confidence: {prediction['confidence']}")
    else:
        print(f"Error: {prediction['error']}")
