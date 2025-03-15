# 📂 Automated File Organizer & Task Executor with LLM Integration  

This Python script **automates file organization**, **compresses files**, and **executes tasks** found in a `todo.txt` file. It leverages **Large Language Models (LLMs)** to analyze tasks and execute them dynamically.  

## ✨ Features  

### 📌 Folder Organization  
- **Scans a folder** and categorizes files into appropriate subfolders:  
  - **PDFs** (`.pdf`)  
  - **Images** (`.jpg`, `.jpeg`, `.png`, `.gif`)  
  - **Code Files** (`.py`, `.js`, `.html`, `.css`, `.cpp`, `.java`)  
  - **Documents** (`.docx`, `.txt`, `.xlsx`, `.csv`)  

### 📌 File Compression  
- **Compresses PDFs** using an online service.  
- **Compresses Images (PNG, JPG)** using an online API.

### 📌 Task Execution from `todo.txt`  
Reads a file named `todo.txt` in the given directory and performs the following tasks **if mentioned inside**:

- **📩 Reminders via Email**  
→ Sends an email with the reminder.

- **📅 Calendar Invites**  
→ Creates and sends a `.ics` calendar invite via email.

- **📈 Stock Price Updates**  
→ Schedules a daily email with NVIDIA stock price.

## 🧠 How LLMs are Used in This Project  
This project **integrates Large Language Models (LLMs) from Gemini AI** to **interpret and automate** tasks.  

### 🔍 **1️⃣ Task Analysis via LLM**  
When a task is found in `todo.txt`, the **LLM analyzes it** and determines:  
- What the task means  
- Which Python function should execute it  
- What parameters should be passed  

⚠️ **LLM-Specific Challenges & Best Practices:** 
1️⃣ Gemini-2 Flash Struggles with Generic & Verbose Prompts
✅ If prompts are too generic, function and variable extraction fails.
✅ If prompts are too verbose, Gemini messes up variable extraction by trying to explain its choices.
✅ Best practice → Keep prompts concise and goal-focused.

### 🚨 **Yahoo Finance API is Unreliable**
- The Yahoo Finance API **often rate-limits requests**, making stock price retrieval inconsistent.  
- It **sometimes fails without warning** and **returns incomplete or outdated data**.  

✅ **Recommended Alternatives:**  
If Yahoo Finance fails too frequently, consider switching to:  
1. **Alpha Vantage** – [https://www.alphavantage.co/](https://www.alphavantage.co/) (Free tier available)  
2. **IEX Cloud** – [https://iexcloud.io/](https://iexcloud.io/) (Real-time pricing)  
3. **Polygon.io** – [https://polygon.io/](https://polygon.io/) (Good for historical data)  

👉 **Modify `get_stock_price()` to use an alternative API** for more reliable data.  


Example:  
#### **Task in `todo.txt`:**
#### **LLM Analysis Output:**
```yaml
Function: remind_me
Variables:
- subject = "Report Submission Reminder"
- body = "Don't forget to submit the report by Sunday."
- to_email = "user@example.com"

