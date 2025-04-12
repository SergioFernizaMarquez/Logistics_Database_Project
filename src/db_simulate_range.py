from db_simulate_daily_activity import simulate_daily_activities
from datetime import datetime, timedelta

def simulate_range(start_date: datetime, num_days: int):
    current_date = start_date
    for _ in range(num_days):
        print(f"Simulating: {current_date.strftime('%Y-%m-%d')}")
        try:
            simulate_daily_activities(current_date)
        except Exception as e:
            print(f"Error on {current_date.strftime('%Y-%m-%d')}: {e}")
        current_date += timedelta(days=1)

if __name__ == "__main__":
    simulate_range(datetime.now().date(), 3652)
