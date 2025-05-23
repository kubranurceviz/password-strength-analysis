# Password Strength Analysis

This project is a Flask web application that analyzes the strength of a user's password. It evaluates whether the password is strong, checks for the inclusion of common words and names, and estimates the time required to crack it.

## Features

- Checks password length, inclusion of uppercase/lowercase letters, digits, and special characters.
- Verifies the password against common passwords, names, and dictionary words.
- Detects repeating or sequential character patterns.
- Estimates how long it would take to crack the password.
- Displays results in JSON format or through a web interface.
- Fetches data from online sources with a 6-hour caching mechanism.

## Requirements

- Python 3.8+
- Flask
- requests
- requests-html

## Installation

```bash
git clone https://github.com/kubranurceviz/password-strength-analysis.git
cd password-strength-analysis
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Usage
Run the application with:


python app.py
Then open your browser and navigate to:


http://127.0.0.1:5000
You can input a password through the web interface or send a request to the API endpoint for JSON output.

Feel free to contribute by creating pull requests or reporting issues.
