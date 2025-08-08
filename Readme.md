# AI-Powered Product Search App

## Overview
This is a Flask-based product catalog app with smart search capabilities enhanced by Google Gemini AI. It filters products from a JSON file and uses AI to understand complex user queries.

---

## How to Run the App

1. **Clone the repository and navigate to the project folder.**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
3.Set your Gemini AI API key as an environment variable:
On Linux/macOS:
  ```bash
export GEMINI_API_KEY="your-real-gemini-key"
```
On Windows (Command Prompt):
```bash
set GEMINI_API_KEY="your-real-gemini-key"
```
On Windows (PowerShell):
```bash
$env:GEMINI_API_KEY="your-real-gemini-key"
```
4.Run the Flask app:

python app.py
Open your browser and go to:
http://127.0.0.1:5000

**AI Feature**
---
The app integrates Google Gemini AI (gemini-1.5-flash) model via the google-generativeai SDK.
The AI interprets natural language search queries and filters products based on strict rules.
If AI is unavailable or errors occur, the app falls back to a local rule-based search.


**How this AI could be integrated with blockchain features?**


This AI-powered product search can be integrated with blockchain by enabling token-gated pricing, where users holding specific tokens get access to exclusive discounts or products. On-chain user preferences can personalize search results securely and transparently, stored directly on the blockchain. Additionally, loyalty smart contracts could automatically reward repeat customers with tokens or benefits based on their purchase history and engagement tracked on-chain.

**Tools and Libraries Used**
---
Flask: Web framework for building the app.

google-generativeai: Official SDK to interact with Google Gemini AI.

Python Standard Libraries: os, json, re for file handling and regex.

Products Data: Stored in a JSON file (products.json) for simplicity.

**Notable Assumptions**
---
The products.json file contains product data with keys: name, category, price, rating, and description.

The Gemini AI key is provided as an environment variable GEMINI_API_KEY.

AI filtering expects the model to return strictly valid JSON arrays with products matching the query constraints.

The app’s AI fallback logic uses regex parsing to interpret price, category, and rating from user queries.

This app is intended for demonstration and development; do not use it as-is for production without proper security and error handling.

