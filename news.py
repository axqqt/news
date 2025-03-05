import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
import schedule
import time

# Define the webhook URL (replace with your actual webhook URL)
WEBHOOK_URL = "https://discord.com/api/webhooks/1339950091120676977/bF_tkDbK8piAaiibeb-RlUAgP4iZPyVcJsqOhJzHIE8rrH3pobmWBzlZs7TFPTi0_6ne"

# Function to convert time from NYT to IST
def convert_nyt_to_ist(nyt_time_str):
    try:
        nyt_tz = pytz.timezone('America/New_York')
        ist_tz = pytz.timezone('Asia/Kolkata')
        today_nyt = datetime.now(nyt_tz).date()

        if nyt_time_str.lower() == 'all day':
            nyt_time = datetime(today_nyt.year, today_nyt.month, today_nyt.day, 0, 0)
        elif nyt_time_str.strip() == '':
            nyt_time = datetime(today_nyt.year, today_nyt.month, today_nyt.day, 0, 0)
        else:
            nyt_time = datetime.strptime(nyt_time_str, '%I:%M%p').time()
            nyt_time = datetime.combine(today_nyt, nyt_time)

        nyt_time = nyt_tz.localize(nyt_time)
        ist_time = nyt_time.astimezone(ist_tz)
        print(f"Converted time: {nyt_time_str} NYT -> {ist_time.strftime('%I:%M %p')} IST")
        return ist_time.strftime('%I:%M %p')
    except Exception as e:
        print(f"Error converting time: {e}")
        return "N/A"

# Function to fetch and filter ForexFactory news
def fetch_forexfactory_news():
    try:
        url = "https://www.forexfactory.com/calendar"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        print("Fetching data from ForexFactory...")
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all rows in the calendar table
        rows = soup.select('.calendar__row.calendar_row')
        print(f"Found {len(rows)} rows in the calendar.")
        filtered_news = []

        for row in rows:
            try:
                impact_icon = row.select_one('.impact__icon')
                if impact_icon and impact_icon['title'] in ['High Impact Expected', 'Moderate Impact Expected']:
                    time_element = row.select_one('.calendar__time.time')
                    time_str = time_element.text.strip() if time_element else '12:00am'
                    currency = row.select_one('.currency').text.strip()
                    event = row.select_one('.calendar__event-title.event').text.strip()
                    impact = impact_icon['title']

                    # Convert time to IST
                    ist_time = convert_nyt_to_ist(time_str)

                    # Append to filtered news
                    filtered_news.append({
                        'time': ist_time,
                        'currency': currency,
                        'event': event,
                        'impact': impact
                    })
                    print(f"Filtered news: {ist_time} - {currency} - {event} - {impact}")
                else:
                    print(f"Ignored news due to low impact or missing data.")
            except Exception as e:
                print(f"Error processing row: {e}")

        print(f"Filtered {len(filtered_news)} relevant news items.")
        return filtered_news
    except Exception as e:
        print(f"Error fetching ForexFactory news: {e}")
        return []

# Function to send notification via webhook
def send_notification(news_items):
    try:
        print("Preparing notification message...")
        # Start the message with a title and emoji for better visibility
        message = "**📊 Forex News Summary (Red & Orange Folders)**\n\n"
        # Loop through each news item and format it nicely
        for item in news_items:
            # Use emojis to indicate impact level
            if item['impact'] == 'High Impact Expected':
                impact_emoji = "🔴"  # Red circle for high impact
            elif item['impact'] == 'Moderate Impact Expected':
                impact_emoji = "🟠"  # Orange circle for moderate impact
            else:
                impact_emoji = "⚪"  # White circle for low or unknown impact

            # Format each news item with Markdown
            message += f"**⏰ Time (IST):** `{item['time']}`\n"
            message += f"**💵 Currency:** `{item['currency']}`\n"
            message += f"**📋 Event:** `{item['event']}`\n"
            message += f"**💥 Impact:** {impact_emoji} `{item['impact']}`\n"
            message += "\n" + "-" * 30 + "\n"  # Add a separator between items

        # Add a footer with the current date
        current_date = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')
        message += f"\n*📅 Last Updated: {current_date} IST*"

        # Prepare the payload for the webhook
        payload = {
            'content': message
        }
        print("Sending notification via webhook...")
        response = requests.post(WEBHOOK_URL, json=payload)

        # Check if the notification was sent successfully
        if response.status_code == 204:
            print("Notification sent successfully!")
        else:
            print(f"Failed to send notification. Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error sending notification: {e}")

# Main function to run the script
def job():
    print("\n--- Starting job ---")
    print("Fetching ForexFactory news...")
    news_items = fetch_forexfactory_news()
    if news_items:
        print("Sending notifications...")
        send_notification(news_items)
    else:
        print("No relevant news found.")
    print("--- Job completed ---\n")

# Schedule the job to run daily at midnight IST
def run_scheduler():
    print("Scheduler started. Waiting for the next job execution...")
    ist_tz = pytz.timezone('Asia/Kolkata')  # Use IST timezone

    while True:
        now = datetime.now(ist_tz)
        if now.hour == 0 and now.minute == 0:  # Run at midnight IST
            job()
            time.sleep(60)  # Sleep for 60 seconds to avoid running multiple times in the same minute
        else:
            print("Checking for pending jobs...")
            time.sleep(1)

if __name__ == "__main__":
    # Test the webhook manually (uncomment the following lines to test)
    # payload = {"content": "Test message from the script!"}
    # response = requests.post(WEBHOOK_URL, json=payload)
    # print(response.status_code, response.text)

    # Run the scheduler
    run_scheduler()