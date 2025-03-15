import os
import shutil
import requests
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import os
import smtplib
import ssl
import base64
from dotenv import load_dotenv
import convertapi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import re
import schedule
import threading
import time

def compress_image(input_path, output_path, quality=60):
    """Compress an image file by reducing quality."""
    img = Image.open(input_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save(output_path, optimize=True, quality=quality)

def categorize_and_move_files(directory, exclude_files=None):
    """Organize files into appropriate category folders, excluding specified files."""
    FILE_CATEGORIES = {
        "PDFs": [".pdf"],
        "Images": [".jpg", ".jpeg", ".png", ".gif"],
        "Code": [".py", ".js", ".html", ".css", ".cpp", ".java"],
        "Documents": [".docx", ".txt", ".xlsx", ".csv"]
    }

    print("\n=== Starting File Organization ===")
    print(f"1. Scanning directory: {directory}")
    print("2. Creating category folders as needed:")
    for category in FILE_CATEGORIES:
        print(f"   - {category}")

    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and (exclude_files is None or file not in exclude_files):
            ext = os.path.splitext(file)[1].lower()
            for category, extensions in FILE_CATEGORIES.items():
                if ext in extensions:
                    category_path = os.path.join(directory, category)
                    os.makedirs(category_path, exist_ok=True)
                    shutil.move(file_path, os.path.join(category_path, file))
                    print(f"✓ Completed: {file} -> {category}/")

    print("\n=== Organization Complete ===")

def compress_images_in_folder(folder_path, quality=60):
    """Compress all images in a given folder using Python image compression libraries.
    
    Args:
        folder_path (str): Path to the folder containing images
        quality (int, optional): Quality percentage (0-100). Defaults to 60.
    """
    print(f"\n=== Starting Image Compression in {folder_path} ===")
    supported_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_extensions:
                print(f"\nCompressing image: {file}")
                try:
                    # Create a compressed version with '_compressed' suffix
                    compressed_path = os.path.join(folder_path, f"compressed_{file}")
                    compress_image(file_path, compressed_path, quality)
                    # Remove original file after successful compression
                    os.remove(file_path)
                    print(f"✓ Removed original file: {file}")
                except Exception as e:
                    print(f"✗ Error compressing {file}: {str(e)}")
    
    print("\n=== Image Compression Complete ===")

def compress_pdf(input_path):
    """Compress a PDF file using ConvertAPI with enhanced error handling.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path to save the compressed PDF file

    """
    load_dotenv()
    api_key = os.getenv('CONVERTAPI_SECRET')
    
    if not api_key:
        raise ValueError("ConvertAPI secret key not found in .env file")
    
    convertapi.api_credentials = api_key

    result = convertapi.convert('compress', {
                'File': input_path
            }, from_format='pdf').save_files(input_path)
        

def compress_pdfs_in_folder(folder_path):
    """Compress all PDFs in a given folder using the updated compress_pdf function with retry logic.
    
    Args:
        folder_path (str): Path to the folder containing PDFs
    """
    print(f"\n=== Starting PDF Compression in {folder_path} ===")
    
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path) and file.lower().endswith('.pdf'):
            attempt = 0
            success = False
            while attempt < 3 and not success:
                try:
                    print(f"\nCompressing PDF: {file} (Attempt {attempt + 1}/3)")
                    # Use the same path for input and output to replace the original file
                    compress_pdf(file_path)
                    print(f"✓ Successfully compressed: {file}")
                    success = True
                except Exception as e:
                    attempt += 1
                    print(f"✗ Error compressing {file} (Attempt {attempt}/3): {str(e)}")
                    if attempt >= 3:
                        print(f"✗ Cannot compress {file} after 3 attempts. Moving on.")
    
    print("\n=== PDF Compression Complete ===")

def send_email(subject, body, to_email, from_email="ajaynadimpallikumar@gmail.com"):
    """Send an email using SMTP."""
    load_dotenv()
    email_password = os.getenv('EMAIL_PASSWORD')  # Your app password
    email_smtp_server = "smtp.gmail.com"
    email_smtp_port = 587

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        # Establish connection to the SMTP server
        server = smtplib.SMTP(email_smtp_server, email_smtp_port)
        server.ehlo()
        server.starttls()  # Secure the connection
        server.ehlo()
        server.login(from_email, email_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def remind_me(subject, body, to_email):
    """Send a reminder email."""
    send_email(subject, body, to_email)

def share_stock_price(to_email, time_str, symbol='NVDA', retries=3, wait_time=5):
    """Share the stock price for a given symbol via email at a scheduled time (sends ASAP if time matches and always schedules)."""
    def get_stock_price():
        """Get the current stock price for the given symbol using Yahoo Finance with retry logic."""
        for attempt in range(retries):
            try:
                data = yf.download(symbol, period="1d")
                print(data["Close"].iloc[-1])
                if data.empty:
                    raise ValueError("Empty stock data returned. Check symbol or try later.")


                return data['open'][0]  # Successfully retrieved price

            except Exception as e:
                
                print(f"❌ Failed to retrieve stock price (Attempt {attempt+1}/{retries}): {str(e)}")

                if "Rate limited" in str(e) or "Too Many Requests" in str(e):
                    wait_time *= 2  # Exponential backoff
                    print(f"🔄 Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    break  # Do not retry for other errors

        print("❌ Unable to fetch stock price after multiple attempts.")
        return None

    def send_stock_email():
        """Send an email with the latest stock price."""
        stock_price = get_stock_price()
        if stock_price is None:
            print("❌ Skipping email: Stock price unavailable.")
            return

        subject = f"{symbol} Stock Price Update"
        body = f"The current stock price for {symbol} is ${stock_price:.2f}."
        send_email(subject, body, to_email)

    try:
        # Validate & convert time
        match = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?\s?(AM|PM)", time_str.strip(), re.IGNORECASE)
        if not match:
            raise ValueError("Invalid time format! Use 'H AM/PM' or 'H:MM AM/PM'.")

        # Convert input time to 24-hour format
        X_PM_24H = datetime.strptime(f"{match.group(1)}:{match.group(2) or '00'} {match.group(3).upper()}", "%I:%M %p").strftime("%H:%M")
        print(f"✅ Scheduling {symbol} stock price email to {to_email} at {X_PM_24H} (24H format)")

        # Get the current time in 24-hour format
        current_time = datetime.now().strftime("%H:%M")

        # Schedule the email for daily execution
        schedule.every().day.at(X_PM_24H).do(send_stock_email)
        print(f"📅 Email scheduled for {X_PM_24H} daily.")

        # If the input time matches the current time, send email ASAP
        if X_PM_24H == current_time:
            print("⏳ Time matches current time! Sending email ASAP...")
            time.sleep(1)  # Small delay to ensure scheduler thread starts
            send_stock_email()  # Immediate execution

        # Run the scheduler in a background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

    except ValueError as e:
        print(f"❌ Error: {e}")
        return  # Exit function if format is invalid

def run_scheduler():
    """Run the scheduler in a separate thread to avoid blocking the main script."""
    while True:
        print(f"🔄 Checking schedule at {datetime.now().strftime('%H:%M:%S')}...")  # Debugging
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def add_calendar_invite(subject, body, to_email, event_start, event_end):
    """Create a calendar invite and send it via email."""
    # If event_start or event_end are strings, parse them into datetime objects
    if isinstance(event_start, str):
        try:
            event_start = datetime.strptime(event_start, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("event_start must be in 'YYYY-MM-DD HH:MM:SS' format")
    if isinstance(event_end, str):
        try:
            event_end = datetime.strptime(event_end, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("event_end must be in 'YYYY-MM-DD HH:MM:SS' format")

    # Ensure event_start and event_end are datetime objects
    if not isinstance(event_start, datetime):
        raise ValueError("event_start must be a datetime object or a string in 'YYYY-MM-DD HH:MM:SS' format")
    if not isinstance(event_end, datetime):
        raise ValueError("event_end must be a datetime object or a string in 'YYYY-MM-DD HH:MM:SS' format")

    # Add timezone information if not already present
    if event_start.tzinfo is None:
        event_start = pytz.utc.localize(event_start)
    if event_end.tzinfo is None:
        event_end = pytz.utc.localize(event_end)

    # Create the calendar and event
    cal = Calendar()
    event = Event()
    event.add('summary', subject)
    event.add('dtstart', event_start)
    event.add('dtend', event_end)
    event.add('description', body)
    cal.add_component(event)

    # Save the .ics file
    ics_file = 'invite.ics'
    with open(ics_file, 'wb') as f:
        f.write(cal.to_ical())
    print(f"✅ Calendar invite saved to {ics_file}")

    # Send the invite via email
    send_email(subject, body, to_email)
    print(f"✅ Calendar invite sent to {to_email}")

# Example usage
if __name__ == "__main__":
    directory = input("Enter the directory path to organize: ")
    # Remove any extra quotes that might be copied from Windows path
    directory = directory.strip('"')
    


