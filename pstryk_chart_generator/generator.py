import os
import sys
import json
import asyncio
import logging
import datetime
from datetime import timedelta
import pytz
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
API_URL = "http://supervisor/core/api"
HEADERS = {"Authorization": f"Bearer {SUPERVISOR_TOKEN}", "Content-Type": "application/json"}

POWER_SENSOR = os.environ.get("POWER_SENSOR", "sensor.tze200_ts0601_active_power")
CHEAP_SENSOR = os.environ.get("CHEAP_SENSOR", "sensor.api_pricing_pstryk_cheapest_buy_hour_today")
EXP_SENSOR = os.environ.get("EXP_SENSOR", "sensor.api_pricing_pstryk_most_expensive_buy_hour_today")

OUTPUT_DIR = "/config/www/pstryk_chart_generator"
CACHE_FILE = os.path.join(OUTPUT_DIR, "trend_cache.json")
CHART_FILE = os.path.join(OUTPUT_DIR, "chart_pstryk.png")
YESTERDAY_CHART_FILE = os.path.join(OUTPUT_DIR, "chart_pstryk_yesterday.png")

TIMEZONE = pytz.timezone("Europe/Warsaw")

def get_ha_state(entity_id):
    url = f"{API_URL}/states/{entity_id}"
    try:
        if not SUPERVISOR_TOKEN:
            logger.warning("No SUPERVISOR_TOKEN! Using dummy data for testing.")
            return None
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"Failed to fetch state for {entity_id}: {e}")
        return None

def get_ha_history(entity_id, start_time, end_time=None):
    url = f"{API_URL}/history/period/{start_time.isoformat()}"
    params = {"filter_entity_id": entity_id, "minimal_response": "true"}
    if end_time:
        params["end_time"] = end_time.isoformat()
    try:
        if not SUPERVISOR_TOKEN:
            return []
        res = requests.get(url, headers=HEADERS, params=params, timeout=30)
        res.raise_for_status()
        data = res.json()
        if data and len(data) > 0:
            return data[0]
        return []
    except Exception as e:
        logger.error(f"Failed to fetch history for {entity_id}: {e}")
        return []

def calculate_trend_14_days(now):
    today_str = now.strftime("%Y-%m-%d")
    
    # Check cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
                if cache.get("date") == today_str:
                    logger.info("Loaded 14-days trend from local cache.")
                    return cache.get("trend")
        except Exception as e:
            logger.error(f"Error reading cache: {e}")

    logger.info("Calculating 14-days trend from HA History API (This might take a moment)...")
    start_time = (now - timedelta(days=14)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    history = get_ha_history(POWER_SENSOR, start_time, now)
    
    if not history:
        logger.warning("No history found for trend calculation.")
        return []

    # Parse and compute hourly average
    df = pd.DataFrame(history)
    if df.empty: return []
    
    df['last_changed'] = pd.to_datetime(df['last_changed'])
    df['state'] = pd.to_numeric(df['state'], errors='coerce')
    df = df.dropna(subset=['state'])
    
    # Set index and group by hour of day
    df = df.set_index('last_changed')
    df.index = df.index.tz_convert(TIMEZONE)
    
    # Calculate average per hour 0-23
    hourly_avg = df.groupby(df.index.hour)['state'].mean()
    
    trend_data = {}
    for hour, val in hourly_avg.items():
        trend_data[str(hour)] = val
        
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({"date": today_str, "trend": trend_data}, f)
        logger.info("Trend calculated and cached successfully.")
    except Exception as e:
        logger.error(f"Failed to write cache: {e}")

    return trend_data

def parse_hour_range(hour_str, now):
    # e.g., "06:00-07:00"
    try:
        parts = hour_str.split('-')
        start_h = int(parts[0].split(':')[0])
        end_h = int(parts[1].split(':')[0])
        
        start_dt = now.replace(hour=start_h, minute=0, second=0, microsecond=0)
        if end_h == 0:
            # e.g., 23:00-00:00 -> up to midnight next day
            end_dt = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end_dt = now.replace(hour=end_h, minute=0, second=0, microsecond=0)
        return start_dt, end_dt
    except Exception:
        return None, None

def render_chart():
    logger.info("Starting chart generation...")
    now = datetime.datetime.now(TIMEZONE)
    
    # 1. Fetch sensor attributes for cheap/expensive hours
    cheap_state = get_ha_state(CHEAP_SENSOR)
    exp_state = get_ha_state(EXP_SENSOR)
    
    cheap_ranges = []
    if cheap_state and 'attributes' in cheap_state and 'all_cheapest_hours' in cheap_state['attributes']:
        for item in cheap_state['attributes']['all_cheapest_hours']:
            h_str = item.get('hour') if isinstance(item, dict) else item
            s_dt, e_dt = parse_hour_range(h_str, now)
            if s_dt and e_dt: cheap_ranges.append((s_dt, e_dt))
            
    exp_ranges = []
    if exp_state and 'attributes' in exp_state and 'all_expensive_hours' in exp_state['attributes']:
        for item in exp_state['attributes']['all_expensive_hours']:
            s_dt, e_dt = parse_hour_range(item, now)
            if s_dt and e_dt: exp_ranges.append((s_dt, e_dt))

    # 2. Fetch today's power history from 06:00
    start_of_chart = now.replace(hour=6, minute=0, second=0, microsecond=0)
    end_of_chart = now.replace(hour=23, minute=59, second=59, microsecond=0)
    if now < start_of_chart:
        # If it's earlier than 06:00, use yesterday's 06:00
        start_of_chart = start_of_chart - timedelta(days=1)
        end_of_chart = end_of_chart - timedelta(days=1)

    history = get_ha_history(POWER_SENSOR, start_of_chart, now)
    
    df_today = pd.DataFrame(history)
    if not df_today.empty:
        df_today['last_changed'] = pd.to_datetime(df_today['last_changed'])
        df_today['state'] = pd.to_numeric(df_today['state'], errors='coerce')
        df_today = df_today.dropna(subset=['state'])
        df_today = df_today.set_index('last_changed')
        df_today.index = df_today.index.tz_convert(TIMEZONE)
    else:
        df_today = pd.DataFrame()

    # 3. Retrieve 14-day trend
    trend_dict = calculate_trend_14_days(now)
    
    # 4. Draw Graphic
    # Dark theme styling matching typical HA dashboards
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='#1c1c1c')
    ax.set_facecolor('#1c1c1c')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#444444')
    ax.spines['left'].set_color('#444444')
    ax.tick_params(colors='#aaaaaa')
    ax.yaxis.grid(True, linestyle='-', color='#333333', alpha=0.5)
    
    # Plot real data
    if not df_today.empty:
        ax.plot(df_today.index, df_today['state'], color='#03a9f4', linewidth=2, label="Bieżace zużycie")
        ax.fill_between(df_today.index, df_today['state'], color='#03a9f4', alpha=0.2)
        
    ax.set_xlim([start_of_chart, end_of_chart])
    
    # Axis formatting
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=0)
    plt.ylabel("kW", color='#aaaaaa', rotation=0, labelpad=15, loc='top')
    plt.title("Zużycie a Taryfy", color='white', loc='left', pad=20, fontsize=16)

    # Shade Cheap / Expensive hours
    for s_dt, e_dt in cheap_ranges:
        if s_dt >= start_of_chart or e_dt <= end_of_chart:
            ax.axvspan(max(s_dt, start_of_chart), min(e_dt, end_of_chart), color='green', alpha=0.15, lw=0)
            
    for s_dt, e_dt in exp_ranges:
        if s_dt >= start_of_chart or e_dt <= end_of_chart:
            ax.axvspan(max(s_dt, start_of_chart), min(e_dt, end_of_chart), color='red', alpha=0.15, lw=0)

    # Future formatting and Trendline
    if now < end_of_chart:
        # Gray overlay for the future
        ax.axvspan(now, end_of_chart, color='#000000', alpha=0.3, zorder=10)
        
        # Plot trendline for the future
        if trend_dict:
            future_times = []
            future_vals = []
            current_dt = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            while current_dt <= end_of_chart:
                hr_str = str(current_dt.hour)
                if hr_str in trend_dict:
                    future_times.append(current_dt)
                    future_vals.append(trend_dict[hr_str])
                current_dt += timedelta(hours=1)
                
            if future_times:
                # To connect neatly, append the last real value if available
                if not df_today.empty:
                    last_real_time = df_today.index[-1]
                    last_real_val = df_today['state'].iloc[-1]
                    future_times.insert(0, last_real_time)
                    future_vals.insert(0, last_real_val)
                    
                ax.plot(future_times, future_vals, color='#888888', linestyle='--', linewidth=1.5, drawstyle='steps-post', label="Prognoza (14 dni)", zorder=11)

    plt.tight_layout()
    plt.savefig(CHART_FILE, dpi=120, transparent=False)
    plt.close()
    
    logger.info(f"Chart saved to {CHART_FILE}")
    
    # End of day copy check (if hour is 23 and minute is 55+)
    if now.hour == 23 and now.minute >= 50: # Triggered around 23:55
        import shutil
        shutil.copyfile(CHART_FILE, YESTERDAY_CHART_FILE)
        logger.info(f"End of day! Saved copy to {YESTERDAY_CHART_FILE}")

def run_job():
    logger.info("Executing scheduled/on-demand chart generation...")
    try:
        render_chart()
    except Exception as e:
        logger.error(f"Error during chart generation: {e}")

# HTTP Handler for Actions (REST Command)
async def handle_generate(request):
    logger.info("Received web request to trigger chart generation!")
    # Call directly, or schedule it independently if we don't want to block HTTP.
    # Running event loop executor for blocking matplotlib rendering
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_job)
    return web.Response(text="Chart generation triggered.\n")

async def init_web_app():
    app = web.Application()
    app.router.add_get('/generate', handle_generate)
    return app

if __name__ == "__main__":
    logger.info("Starting up App...")
    
    # Try one initial run to ensure cache works and first image is there
    run_job()

    # Set up scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_job, 'cron', minute=55)
    scheduler.start()
    
    # Set up and run web server
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_web_app())
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    
    # By default, use port 8099
    site = web.TCPSite(runner, '0.0.0.0', 8099)
    loop.run_until_complete(site.start())
    
    logger.info("Scheduler and HTTP Action Server are running. Waiting for tasks...")
    
    # Run forever
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
