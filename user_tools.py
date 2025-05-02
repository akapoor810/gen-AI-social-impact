from flask import send_file
import threading
import schedule
import time
import os
import json
from flask import Flask, request, jsonify, Response
from llmproxy import *
import re
from duckduckgo_search import DDGS 
from bs4 import BeautifulSoup
import requests
import random

#WEEKLY TOOL FUNCTIONS
def websearch(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
    return [r["href"] for r in results]

def get_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        # Remove non-content tags for a cleaner text
        for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        return " ".join(text.split())[:1500]
    return f"Failed to fetch {url}, status code: {response.status_code}"

def youtube_search(query):
    with DDGS() as ddgs:
        results = ddgs.text(f"{query} site:youtube.com", max_results=5)
    return [r["href"] for r in results if "youtube.com/watch" in r["href"]]

def tiktok_search(query):
    with DDGS() as ddgs:
        results = ddgs.text(f"{query} site:tiktok.com", max_results=5)
    return [r["href"] for r in results if "tiktok.com" in r["href"]]

def instagram_search(query):
    hashtag = query.replace(" ", "")
    with DDGS() as ddgs:
        results = ddgs.text(f"#{hashtag} site:instagram.com", max_results=5)
    return [r["href"] for r in results if "instagram.com" in r["href"]]

# --- TOOL PARSER ---
def extract_tool(text):
    for tool in ["websearch", "get_page", "youtube_search", "tiktok_search", "instagram_search"]:
        match = re.search(fr'{tool}\([^)]*\)', text)
        if match:
            return match.group()
    
    return


# --- SEND EMAIL FUNCTION ---
def send_email(dst, subject, content):
    print("destination email", dst)
    print("subject", subject)
    print("content", content)

    import os, smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import json
 
    # Email configuration
    smtp_server = "smtp-tls.eecs.tufts.edu"  # e.g., mail.yourdomain.com
    smtp_port = 587  # Usually 587 for TLS, 465 for SSL
    sender_email = "akapoo02@eecs.tufts.edu"
    receiver_email = dst
    password = "anikacs@tufts810"

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    body = content
    msg.attach(MIMEText(body, "plain"))

    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection (use only if the server supports TLS)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return "Email sent successfully!"
    except Exception as e:
        print("there was an error")
        return f"Error: {e}" 
    


### --- RAG UPLOAD FUNCTION --- ###
def rag_upload(condition, user, session_dict):
    sid = session_dict[user]["session_id"]
    if "diabetes" in condition.lower():
        pdf_upload(path = 'HCS-Booklet-Diabetes Type 2 Guidebook.pdf',
        session_id = sid,
        strategy = 'smart')
        
        pdf_upload(path = 'standards-of-care-2023.pdf',
        session_id = sid,
        strategy = 'smart')
    
    else:
        pdf_upload(path = 'ACG-Crohns-Guideline-Summary.pdf',
        session_id = sid,
        strategy = 'smart')

        pdf_upload(path = 'crohns-disease.pdf',
        session_id = sid,
        strategy = 'smart')

        pdf_upload(path = 'living-with-crohns-disease.pdf',
        session_id = sid,
        strategy = 'smart')