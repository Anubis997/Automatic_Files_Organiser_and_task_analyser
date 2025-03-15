import google.generativeai as genai
import os
from dotenv import load_dotenv
from google.cloud import secretmanager
import warnings
import logging
from Root_functions import (
    categorize_and_move_files,
    compress_pdfs_in_folder,
    compress_images_in_folder,
    remind_me,
    add_calendar_invite,
    share_stock_price,
    send_email
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import sys
from datetime import datetime
import pytz
import time

def configure_environment():
    """Configure environment and logging settings."""

    # Suppress absl logging
    try:
        import absl.logging
        absl.logging.set_verbosity(absl.logging.ERROR)
        # Prevent absl from writing to stderr
        absl.logging.get_absl_handler().setLevel(absl.logging.ERROR)
    except ImportError:
        pass

    
    # Load environment variables from .env file
    load_dotenv()

def get_api_key():
    """Retrieve API key from environment variable."""
    return os.getenv("GEMINI_API_KEY")

def initialize_llms(api_key):
    """Initialize and configure both LLMs with the provided API key."""
    genai.configure(api_key=api_key)
    return (
        genai.GenerativeModel('gemini-2.0-flash'),  # organizer_llm
        genai.GenerativeModel('gemini-2.0-flash')   # task_analyzer_llm
    )

def read_root_functions():
    """Read and return the content of Root_functions.py."""
    with open("Root_functions.py", "r", encoding="utf-8") as file:
        return file.read()

def read_to_do_tasks(directory_path):
    """Read and return the content of to_do.txt from the specified directory."""
    # Normalize the directory path to remove any extra quotes
    directory_path = os.path.normpath(directory_path.strip('"\'').strip())
    to_do_path = os.path.join(directory_path, "to_do.txt")
    try:
        with open(to_do_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("to_do.txt not found in the specified directory.")
        return []
    except OSError as e:
        print(f"Error opening to_do.txt: {e}")
        return []

def analyze_tasks_with_llm(task_analyzer_llm, tasks, root_functions_content):
    """Use LLM to analyze tasks, suggest functions, and execute based on user confirmation."""
    for task in tasks:
        task_prompt = f"""Given these functions from Root_functions.py:
        {root_functions_content}
        
        For the task: "{task}", determine the most appropriate function in Root_functions.py to use. 
        I just want these, please don't include anything else.
        Example:
        Task: Remind me to "Do EPAI Assignment by Sunday" via email. My email is ajaynadimpallikumar@gmail.com
        Function: remind_me
        Variables:
        - subject = "EPAI Assignment Reminder"
        - body = "Don't forget to do the EPAI Assignment by Sunday."
        - to_email = "ajaynadimpallikumar@gmail.com"
        - X_PM = "6 PM"  # Add this line to include the scheduled time
        
        """
        
        analysis = task_analyzer_llm.generate_content(task_prompt)
        
        # Extract and print only the relevant parts
        print("\n=== Task Analysis ===")
        print(analysis.text.strip())

        # Ask for user confirmation immediately after analysis
        proceed = input(f"\nShould I proceed with the task? (yes/no): ")
        if proceed.lower() == 'yes':
            # Execute the function using the provided analysis
            execute_from_analysis(analysis.text)


def execute_from_analysis(task_analysis):
    """Execute the function based on the task analysis."""
    lines = task_analysis.splitlines()
    function_name = None
    variables = {}

    # Regular expression to match variable lines
    var_pattern = re.compile(r'-\s*(\w+)\s*=\s*(.+)')

    for line in lines:
        if line.startswith("Function:"):
            function_name = line.split(":", 1)[1].strip()
        elif line.startswith("Variables:"):
            continue
        elif line.strip().startswith("-"):
            match = var_pattern.match(line.strip())
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip().strip('"').strip("'")
                # Remove text within parentheses
                value = re.sub(r'\(.*?\)', '', value).strip()
                variables[key] = value

    # Debugging: Print extracted variables
    print(f"Function: {function_name}")
    print("Variables:", variables)

    # Convert date strings to datetime objects
    datetime_format = "%Y-%m-%d %H:%M:%S"
    try:
        for key in ['event_start', 'event_end']:
            if key in variables:
                # Ensure we strip any non-date text like "datetime:"
                date_str = re.sub(r'[^0-9\-:\s]', '', variables[key]).strip()

                # Check if the string has seconds, otherwise append ":00"
                if len(date_str) == 16:  # Format like '2025-03-09 14:00'
                    date_str += ":00"

                # Convert to datetime object
                variables[key] = datetime.strptime(date_str, datetime_format).replace(tzinfo=pytz.UTC)
    
    except ValueError as e:
        print(f"❌ Error parsing datetime: {str(e)}")
        return

    # Handle execution of the correct function
    try:
        if function_name == "add_calendar_invite":
            add_calendar_invite(
                variables["subject"],
                variables["body"],
                variables["to_email"],
                variables["event_start"],
                variables["event_end"]
            )
        elif function_name == "share_stock_price":
            # Ensure symbol is included, default to 'NVDA' if missing
            share_stock_price(
                to_email=variables["to_email"], 
                time_str=variables.get("time_str", "6 PM"),
                symbol=variables.get("symbol", "NVDA")  # Include symbol dynamically
            )
        elif function_name == "remind_me":
            remind_me(
                variables["subject"],
                variables["body"],
                variables["to_email"]
            )
        elif function_name == "send_email":
            send_email(
                variables["subject"],
                variables["body"],
                variables["to_email"]
            )
        else:
            print(f"⚠️ Function {function_name} is not recognized or not implemented.")

    except Exception as e:
        print(f"❌ Error executing function {function_name}: {str(e)}")

def organize_folder(directory_path, organizer_llm, root_functions_content):
    """Organize files in the specified directory based on LLM analysis."""
    directory_path = os.path.normpath(directory_path.strip('"\'').strip())
    if not os.path.exists(directory_path):
        print(f"Error: Directory not found: {directory_path}")
        return
    
    tasks = [
        "Organize files into appropriate category folders",
        "Compress PDF files",
        "Compress image files"
    ]
    
    task_prompt = f"""Given these functions from Root_functions.py:
    {root_functions_content}
    
    For each task, tell me which function would be most appropriate and why:
    
    Tasks:
    1. {tasks[0]}
    2. {tasks[1]}
    3. {tasks[2]}
    
    Format your response as:
    Task 1: [Task 1] - [function name] - [explanation]
    Task 2: [Task 2] - [function name] - [explanation]
    Task 3: [Task 3] - [function name] - [explanation]"""
    
    analysis = organizer_llm.generate_content(task_prompt)
    print("\n=== Function Analysis ===")    
    try:
        # Extract function names and explanations from the analysis
        lines = analysis.text.strip().splitlines()
        task_functions = {}
        for line in lines:
            if line.startswith("Task"):
                parts = line.split(" - ")
                if len(parts) >= 3:
                    task = parts[0].split(": ")[1].strip()
                    function_name = parts[1].strip()
                    explanation = parts[2].strip()
                    task_functions[task] = (function_name, explanation)
        
        # Execute tasks based on user confirmation
        for task in tasks:
            if task in task_functions:
                function_name, explanation = task_functions[task]
                print(f"\nTask: {task}")
                print(f"Function: {function_name}")
                proceed = input(f"Should I proceed with this task? (yes/no): ")
                if proceed.lower() == 'yes':
                    if task == "Organize files into appropriate category folders":
                        categorize_and_move_files(directory_path, exclude_files=["to_do.txt"])
                    elif task == "Compress PDF files":
                        pdfs_folder = os.path.join(directory_path, "PDFs")
                        if os.path.exists(pdfs_folder):
                            compress_pdfs_in_folder(pdfs_folder)
                    elif task == "Compress image files":
                        images_folder = os.path.join(directory_path, "Images")
                        if os.path.exists(images_folder):
                            compress_images_in_folder(images_folder)
        
        print("\nAll requested operations completed!")
    except Exception as e:
        print(f"Error during execution: {str(e)}")

def main():
    """Main function to run the organization script."""
    configure_environment()
    api_key = get_api_key()
    organizer_llm, task_analyzer_llm = initialize_llms(api_key)
    root_functions_content = read_root_functions()
    
    # First, analyze tasks in to_do.txt
    directory_path = input("Enter the directory path to organize: ")
    tasks = read_to_do_tasks(directory_path)
    if tasks:
        analyze_tasks_with_llm(task_analyzer_llm, tasks, root_functions_content)
    
    # Then, handle directory organization
    organize_folder(directory_path, organizer_llm, root_functions_content)
    
    # Keep the main program alive while the scheduler is running
    try:
        while True:
            time.sleep(1)  # Avoid excessive CPU usage
    except KeyboardInterrupt:
        print("\nProgram terminated by user. Exiting...")

if __name__ == "__main__":
    main()

