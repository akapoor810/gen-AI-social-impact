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
# --- TOOL FUNCTIONS ---
def websearch(query):
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=20)
    links = []
    for r in results:
        url = r.get("href") or r.get("url")
        if not url or "duckduckgo.com" in url:
            continue
        links.append(url)
        if len(links) >= 5:
            break
    return links

def youtube_search(query):
    """
    Only fetch actual YouTube video URLs matching the query.
    """
    # wrap the query in quotes for exact-phrase matching
    ddg_query = f'site:youtube.com/watch "{query}"'
    with DDGS() as ddgs:
        results = ddgs.text(ddg_query, max_results=30)
    links = []
    for r in results:
        url = r.get("href") or r.get("url")
        if url and ("youtube.com/watch" in url or "youtu.be/" in url):
            links.append(url)
        if len(links) >= 5:
            break
    return links

def tiktok_search(query):
    """
    Only fetch TikTok video URLs matching the query.
    """
    ddg_query = f'site:tiktok.com/video "{query}"'
    with DDGS() as ddgs:
        results = ddgs.text(ddg_query, max_results=30)
    links = []
    for r in results:
        url = r.get("href") or r.get("url")
        if url and "/video/" in url and "tiktok.com" in url:
            links.append(url)
        if len(links) >= 5:
            break
    return links

def instagram_search(query):
    """
    Only fetch Instagram Reel or post URLs matching the query.
    """
    ddg_query = f'site:instagram.com/reel "{query}"'
    with DDGS() as ddgs:
        results = ddgs.text(ddg_query, max_results=30)
    links = []
    for r in results:
        url = r.get("href") or r.get("url")
        if url and "instagram.com" in url and ("/reel/" in url or "/p/" in url):
            links.append(url)
        if len(links) >= 5:
            break
    return links

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
