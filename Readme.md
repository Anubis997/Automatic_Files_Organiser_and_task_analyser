# 📂 Automated File Organizer & Task Executor with LLM Integration  

This Python script **automates file organization**, **compresses files**, and **executes tasks** found in a `todo.txt` file. It leverages **Large Language Models (LLMs)** to analyze tasks and execute them dynamically.  

---

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

---

## 🧠 How LLMs are Used in This Project  

This project **integrates Large Language Models (LLMs) from Gemini AI** to **interpret and automate** tasks.  

### 🔍 **1️⃣ Task Analysis via LLM**  
When a task is found in `todo.txt`, the **LLM analyzes it** and determines:  
- What the task means  
- Which Python function should execute it  
- What parameters should be passed  

Example:  
#### **Task in `todo.txt`:**
#### **LLM Analysis Output:**
```yaml
Function: remind_me
Variables:
- subject = "Report Submission Reminder"
- body = "Don't forget to submit the report by Sunday."
- to_email = "user@example.com"


