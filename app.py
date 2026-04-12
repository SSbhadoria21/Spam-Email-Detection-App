from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

import firebase_admin
from firebase_admin import credentials, firestore

import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Allow HTTP for local dev
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'  # Prevent crash if Google returns scopes in different order

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# --- ML Model Training ---
print("Training ML Model on mail_data.csv...")
data = pd.read_csv("mail_data.csv")
data = data.dropna(subset=['Message', 'Category'])
X = data["Message"]
y = data["Category"].str.upper()

vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X_vec = vectorizer.fit_transform(X)

model = MultinomialNB()
model.fit(X_vec, y)
print("ML Model training complete.")

# Initialize Firestore
db = None
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate('firebase_credentials.json')
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized successfully.")
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase Admin: {e}")

import re

def categorize_spam(message):
    """Categorize spam based on keyword heuristics."""
    message_lower = message.lower()
    
    scam_patterns = {
        "Delivery Scam": [r"package", r"delivery", r"courier", r"dhl", r"fedex", r"usps", r"address.*incomplete", r"redelivery", r"parcel"],
        "Investment/Crypto Scam": [r"investment", r"crypto", r"bitcoin", r"double your money", r"guaranteed profit", r"wallet", r"earnings"],
        "Phishing/Account Verification": [r"verify your account", r"account suspended", r"password reset", r"unauthorized access", r"login attempt", r"action required", r"bank"],
        "Lottery/Prize Scam": [r"lottery", r"prize", r"winner", r"congratulations", r"won", r"claim your", r"jackpot", r"reward"],
        "Invoice/Billing Scam": [r"invoice", r"billing", r"subscription", r"auto-renew", r"payment received", r"receipt", r"norton", r"mcafee"]
    }
    
    for category, patterns in scam_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return category
    
    return "General Spam"

def predict_spam(message):
    if not message or not isinstance(message, str):
        message = ""
    msg_vec = vectorizer.transform([message])
    prediction = model.predict(msg_vec)[0]
    probs = model.predict_proba(msg_vec)[0]
    spam_index = list(model.classes_).index("SPAM")
    
    # Always return spam probability as score (high = spam, low = safe)
    spam_score = round(probs[spam_index] * 100, 1)
    
    category = None
    if prediction == "SPAM":
        category = categorize_spam(message)
        
    return prediction, spam_score, category


def save_to_history(sender, message, result, score, category=None, source="manual", gmail_id=None):
    """Save scan result to Firestore history."""
    if not db:
        print("Firestore not initialized, cannot save history.")
        return
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        doc_data = {
            'user_email': user_email,
            'Date': datetime.now().isoformat(),
            'Sender': sender,
            'Message': message[:200],
            'Result': result,
            'Score': score,
            'Category': category if category else "N/A",
            'Source': source
        }
        if gmail_id:
            doc_data['gmail_id'] = gmail_id
            
        db.collection('history').add(doc_data)
    except Exception as e:
        print(f"Error saving to Firestore history: {e}")


# --- Gmail API Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    score = None
    email_text = ""
    error = None

    if request.method == "POST":
        email_text = request.form.get("email_text", "")
        if email_text.strip():
            result, raw_score, category = predict_spam(email_text)
            score = f"{raw_score}%"
        else:
            error = "Please enter some text."

    return render_template("index.html", result=result, score=score, email_text=email_text, error=error)


@app.route("/fetch_gmail", methods=["POST"])
def fetch_gmail():
    error = None
    emails_data = []
    
    try:
        service = get_gmail_service()
        # 1. Fetch the last 20 messages
        results = service.users().messages().list(userId='me', maxResults=20).execute()
        messages = results.get('messages', [])
        
        if not messages:
            error = "No recent messages found in your Gmail inbox."
        else:
            new_emails = []
            # Fetch details for each message
            for m in messages:
                msg_id = m['id']
                try:
                    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                    snippet = msg.get('snippet', '')
                    
                    # Extract Sender Name from headers
                    headers = msg.get('payload', {}).get('headers', [])
                    sender = "Unknown Sender"
                    for h in headers:
                        if h.get('name', '').lower() == 'from':
                            sender = h.get('value')
                            break
                            
                    new_emails.append({'Sender': sender, 'Message': snippet})
                    
                except Exception as inner_e:
                    print(f"Error fetching message {msg_id}: {inner_e}")
                    continue
                    
            # Remove duplicate snippets right away before prediction
            seen_snippets = set()
            unique_new_emails = []
            for email in new_emails:
                if email['Message'] not in seen_snippets:
                    unique_new_emails.append(email)
                    seen_snippets.add(email['Message'])
            
            for email in unique_new_emails:
                sender = email['Sender']
                snippet = email['Message']
                
                prediction, raw_score, category = predict_spam(snippet)
                
                emails_data.append({
                    'sender': sender,
                    'snippet': snippet,
                    'result': prediction,
                    'score': f"{raw_score}%",
                    'category': category
                })
            
    except Exception as e:
        error = f"Gmail Fetch Error: {str(e)}"
        
    return render_template("index.html", emails=emails_data, error=error)


# --- Google OAuth Authentication Routes ---

def get_google_flow():
    """Create a Google OAuth2 flow for web login."""
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError(
            "Google OAuth credentials file 'credentials.json' not found. "
            "Please download it from the Google Cloud Console (APIs & Services > Credentials) "
            "and place it in the project root directory."
        )

    # Read credentials.json and adapt for web flow
    with open('credentials.json', 'r') as f:
        cred_data = json.load(f)

    # Support both 'installed' and 'web' credential types
    cred_section = cred_data.get('installed') or cred_data.get('web')
    if not cred_section:
        raise ValueError(
            "Invalid credentials.json format. Expected 'installed' or 'web' key."
        )

    # Convert credentials to web flow format
    client_config = {
        'web': {
            'client_id': cred_section['client_id'],
            'client_secret': cred_section['client_secret'],
            'auth_uri': cred_section['auth_uri'],
            'token_uri': cred_section['token_uri'],
            'redirect_uris': ['http://localhost:5000/api/auth/google/callback']
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri='http://localhost:5000/api/auth/google/callback'
    )
    return flow


@app.route("/api/auth/google/login", methods=["GET"])
def google_login():
    """Redirect user to Google OAuth consent screen."""
    try:
        flow = get_google_flow()
    except FileNotFoundError as e:
        return jsonify({
            "error": "credentials_missing",
            "message": str(e)
        }), 503
    except (ValueError, KeyError) as e:
        return jsonify({
            "error": "credentials_invalid",
            "message": f"Invalid credentials.json: {str(e)}"
        }), 503
    except Exception as e:
        return jsonify({
            "error": "oauth_setup_failed",
            "message": f"OAuth setup error: {str(e)}"
        }), 500

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    # Store state and PKCE code_verifier in session for callback
    session['oauth_state'] = state
    session['code_verifier'] = flow.code_verifier
    return redirect(authorization_url)


@app.route("/api/auth/google/callback", methods=["GET"])
def google_callback():
    """Handle Google OAuth callback, fetch user info, save token."""
    flow = get_google_flow()
    # Restore PKCE code_verifier from session
    flow.code_verifier = session.pop('code_verifier', None)
    flow.fetch_token(authorization_response=request.url)
    
    credentials = flow.credentials
    
    # Save token for Gmail API access
    with open('token.json', 'w') as token_file:
        token_file.write(credentials.to_json())
    
    # Get user info from Google
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    
    try:
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        session['user'] = {
            'email': user_info.get('email', ''),
            'name': user_info.get('name', user_info.get('email', '').split('@')[0]),
            'picture': user_info.get('picture', '')
        }
        
        # Save to firestore
        if db:
            try:
                user_email_key = session['user']['email']
                if user_email_key:
                    db.collection('users').document(user_email_key).set(session['user'], merge=True)
            except Exception as e:
                print(f"Error saving user profile to Firestore: {e}")
                
    except Exception as e:
        print(f"Error fetching user info: {e}")
        session['user'] = {
            'email': 'user@gmail.com',
            'name': 'User',
            'picture': ''
        }
    
    # Redirect to frontend dashboard
    return redirect('http://localhost:8080/dashboard')


@app.route("/api/auth/user", methods=["GET"])
def get_user():
    """Return current authenticated user info."""
    user = session.get('user')
    if user:
        return jsonify({"authenticated": True, "user": user})
    return jsonify({"authenticated": False, "user": None})


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    """Clear user session."""
    session.pop('user', None)
    return jsonify({"status": "logged_out"})


# --- JSON API Routes for React Frontend ---

@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json()
    email_text = data.get("email_text", "") if data else ""

    if not email_text.strip():
        return jsonify({"error": "Please enter some text."}), 400

    result, score, category = predict_spam(email_text)
    
    # Save to CSV history
    save_to_history("Manual Input", email_text, result, score, category=category, source="manual")
    
    return jsonify({
        "result": result,
        "score": score,
        "category": category,
        "isSpam": result == "SPAM"
    })


@app.route("/api/fetch-gmail", methods=["POST"])
def api_fetch_gmail():
    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', maxResults=20).execute()
        messages = results.get('messages', [])

        if not messages:
            return jsonify({"emails": [], "message": "No recent messages found."})

        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        seen_gmail_ids = set()
        seen_snippets = set()

        if db:
            docs = db.collection('history').where("user_email", "==", user_email).stream()
            for doc in docs:
                d = doc.to_dict()
                if 'gmail_id' in d:
                    seen_gmail_ids.add(d['gmail_id'])
                else:
                    seen_snippets.add((d.get('Sender', ''), str(d.get('Message', ''))[:200]))

        emails_data = []
        for m in messages:
            msg_id = m['id']
            if msg_id in seen_gmail_ids:
                continue

            try:
                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                snippet = msg.get('snippet', '')

                headers = msg.get('payload', {}).get('headers', [])
                sender = "Unknown Sender"
                subject = "(No Subject)"
                for h in headers:
                    if h.get('name', '').lower() == 'from':
                        sender = h.get('value')
                    if h.get('name', '').lower() == 'subject':
                        subject = h.get('value')

                if (sender, snippet[:200]) in seen_snippets:
                    continue

                prediction, score, category = predict_spam(snippet)
                
                # Save each scanned email to CSV history
                save_to_history(sender, snippet, prediction, score, category=category, source="gmail", gmail_id=msg_id)
                
                emails_data.append({
                    'sender': sender,
                    'subject': subject,
                    'snippet': snippet,
                    'result': prediction,
                    'score': score,
                    'category': category,
                    'isSpam': prediction == "SPAM"
                })
            except Exception as inner_e:
                print(f"Error fetching message {msg_id}: {inner_e}")
                continue

        return jsonify({"emails": emails_data})

    except Exception as e:
        return jsonify({"error": f"Gmail Fetch Error: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return scan history from Firestore."""
    if not db:
        return jsonify({"history": [], "error": "Firestore not initialized."})
    
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        docs = db.collection('history').where("user_email", "==", user_email).stream()
        
        all_docs = []
        for doc in docs:
            all_docs.append(doc)
            
        all_docs.sort(key=lambda d: d.to_dict().get('Date', ''), reverse=True)
        all_docs = all_docs[:200]
        
        history = []
        
        for doc in all_docs:
            doc_dict = doc.to_dict()
            msg = str(doc_dict.get('Message', ''))
            
            history.append({
                'id': doc.id,
                'date': str(doc_dict.get('Date', '')),
                'sender': str(doc_dict.get('Sender', 'Unknown')),
                'message': msg,
                'result': str(doc_dict.get('Result', '')),
                'score': float(doc_dict.get('Score', 0)),
                'category': str(doc_dict.get('Category', 'N/A')),
                'source': str(doc_dict.get('Source', 'manual')),
                'isSpam': str(doc_dict.get('Result', '')).upper() == 'SPAM'
            })
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e), "history": []})

@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    """Clear scan history from Firestore."""
    if not db:
        return jsonify({"status": "error", "message": "Firestore not initialized."})
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        
        # Use get() instead of stream() to prevent iterator mutation issues and use batch for reliability
        docs = db.collection('history').where("user_email", "==", user_email).get()
        
        if docs:
            batch = db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/analytics/charts", methods=["GET"])
def api_analytics_charts():
    """Generate Matplotlib charts for user analytics."""
    if not db:
        return jsonify({"error": "Firestore not initialized."})
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        docs = db.collection('history').where("user_email", "==", user_email).stream()
        
        spam_count = 0
        safe_count = 0
        categories = {}
        
        for doc in docs:
            d = doc.to_dict()
            res = str(d.get('Result', '')).upper()
            if res == 'SPAM':
                spam_count += 1
                cat = d.get('Category', 'General Spam')
                if not cat or cat == "N/A":
                    cat = "General Spam"
                categories[cat] = categories.get(cat, 0) + 1
            else:
                safe_count += 1
                
        if spam_count == 0 and safe_count == 0:
            return jsonify({"charts": None, "message": "No data available."})
            
        # 1. Pie Chart (Spam vs Safe)
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        # Custom colors to match the app theme
        colors = ['#EF4444', '#10B981'] # Red for spam, Green for safe
        ax1.pie([spam_count, safe_count], labels=['Spam', 'Safe'], autopct='%1.1f%%', startangle=90, colors=colors, textprops={'color':"w"})
        ax1.axis('equal') 
        fig1.patch.set_alpha(0.0) # Transparent background
        
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png', transparent=True)
        buf1.seek(0)
        chart_ratio = base64.b64encode(buf1.read()).decode('utf-8')
        plt.close(fig1)
        
        # 2. Bar Chart (Categories)
        chart_categories = None
        if categories:
            fig2, ax2 = plt.subplots(figsize=(6, 4))
            cats = list(categories.keys())
            c_vals = list(categories.values())
            ax2.bar(cats, c_vals, color='#8B5CF6') # Purple accent color
            ax2.tick_params(axis='x', colors='white')
            ax2.tick_params(axis='y', colors='white')
            ax2.spines['bottom'].set_color('white')
            ax2.spines['left'].set_color('white')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            plt.xticks(rotation=15, ha='right')
            fig2.patch.set_alpha(0.0)
            ax2.set_facecolor((0, 0, 0, 0))
            
            plt.tight_layout()
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png', transparent=True)
            buf2.seek(0)
            chart_categories = base64.b64encode(buf2.read()).decode('utf-8')
            plt.close(fig2)
            
        return jsonify({
            "charts": {
                "ratio": chart_ratio,
                "categories": chart_categories
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)})
@app.route("/api/analytics/custom", methods=["GET"])
def api_analytics_custom():
    """Generate dynamic matched Custom Matplotlib chart."""
    if not db:
        return jsonify({"error": "Firestore not initialized."})
        
    metric = request.args.get("metric", "ratio") # ratio, categories, timeline
    chart_type = request.args.get("type", "pie") # pie, bar, doughnut, line
    
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        docs = db.collection('history').where("user_email", "==", user_email).stream()
        
        history_data = []
        for doc in docs:
            history_data.append(doc.to_dict())
            
        if len(history_data) == 0:
            return jsonify({"chart": None, "empty": True, "message": "No data available."})
            
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # 1. Evaluate Metric
        if metric == "ratio":
            spam_count = sum(1 for d in history_data if str(d.get('Result', '')).upper() == 'SPAM')
            safe_count = len(history_data) - spam_count
            labels = ['Spam', 'Safe']
            values = [spam_count, safe_count]
            colors = ['#EF4444', '#10B981']
        elif metric == "categories":
            cats = {}
            for d in history_data:
                if str(d.get('Result', '')).upper() == 'SPAM':
                    c = d.get('Category', 'General Spam')
                    if not c or c == "N/A":
                        c = "General Spam"
                    cats[c] = cats.get(c, 0) + 1
            labels = list(cats.keys()) if cats else ["No Spam"]
            values = list(cats.values()) if cats else [1]
            colors = ['#8B5CF6', '#EC4899', '#F59E0B', '#10B981', '#EF4444']
        elif metric == "timeline":
            dates = {}
            for d in history_data:
                try:
                    date_str = str(d.get('Date', ''))[:10]
                    if date_str:
                        dates[date_str] = dates.get(date_str, 0) + 1
                except: pass
            
            sorted_dates = sorted(dates.keys())
            labels = sorted_dates if sorted_dates else ["Today"]
            values = [dates[k] for k in sorted_dates] if sorted_dates else [0]
            colors = ['#3B82F6']
        else:
            return jsonify({"error": "Invalid metric."})
            
        # 2. Render Chart Type
        if chart_type == "pie":
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)], textprops={'color':"w"})
            ax.axis('equal')
        elif chart_type == "doughnut":
            ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)], textprops={'color':"w"}, wedgeprops=dict(width=0.4, edgecolor='none'))
            ax.axis('equal')
        elif chart_type == "bar":
            # For bar chart, we can safely just loop or pass single color
            cc = colors if len(colors) >= len(labels) else (colors*(len(labels)//len(colors)+1))[:len(labels)]
            ax.bar(labels, values, color=cc)
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(rotation=15, ha='right')
        elif chart_type == "line":
            ax.plot(labels, values, marker='o', color='#3B82F6', linewidth=2, markersize=8)
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(rotation=45, ha='right')
            ax.grid(color='#334155', linestyle='-', linewidth=0.5, alpha=0.5)

        fig.patch.set_alpha(0.0)
        if chart_type in ["bar", "line"]:
            ax.set_facecolor((0, 0, 0, 0))
            
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        buf.seek(0)
        chart_b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        return jsonify({
            "chart": chart_b64,
            "empty": False
        })
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
   app.run(debug=True, host="0.0.0.0", port=5000)