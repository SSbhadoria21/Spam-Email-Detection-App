from flask import Flask, request, jsonify, session, redirect, send_from_directory
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

DIST_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
app = Flask(__name__, static_folder=None)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
CORS(app, supports_credentials=True)

# --- ML Model Training ---
def train_ml_model():
    """Load data and train the Multinomial Naive Bayes model."""
    try:
        print("Training ML Model on mail_data.csv...")
        if os.path.exists("mail_data.csv"):
            data = pd.read_csv("mail_data.csv")
        else:
            print("Warning: mail_data.csv not found. Using minimal fallback dataset.")
            # Tiny fallback dataset so the app can still boot and function basically
            fallback_data = {
                'Message': ['Congratulations you won a prize', 'Meeting at 5pm today', 'Invest now for big profits', 'Hello, how are you?'],
                'Category': ['spam', 'ham', 'spam', 'ham']
            }
            data = pd.DataFrame(fallback_data)
        
        data = data.dropna(subset=['Message', 'Category'])
        X = data["Message"]
        y = data["Category"].str.upper()

        vec = TfidfVectorizer(stop_words='english', max_features=5000)
        X_vec = vec.fit_transform(X)

        mdl = MultinomialNB()
        mdl.fit(X_vec, y)
        print("ML Model training complete.")
        return vec, mdl
    except Exception as e:
        print(f"Critial error during ML training: {e}")
        # Return dummy objects if training fails completely
        return TfidfVectorizer().fit(["placeholder"]), MultinomialNB().fit([[0]], ["HAM"])

vectorizer, model = train_ml_model()

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


def save_to_history(sender, message, result, score, category=None, source="manual", gmail_id=None, subject=None, date_val=None, doc_id=None):
    """Save scan result to Firestore history."""
    if not db:
        print("Firestore not initialized, cannot save history.")
        return
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        doc_data = {
            'user_email': user_email,
            'Date': date_val if date_val else datetime.now().isoformat(),
            'Sender': sender,
            'Subject': subject if subject else '(No Subject)',
            'Message': message[:200],
            'Result': result,
            'Score': score,
            'Category': category if category else "N/A",
            'Source': source
        }
        if gmail_id:
            doc_data['gmail_id'] = gmail_id
            
        if doc_id:
            db.collection('history').document(doc_id).set(doc_data)
        else:
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





# --- Google OAuth Authentication Routes ---

# --- Production Session Hardening ---
# Required for cross-domain auth (Vercel -> Render)
if os.getenv("RENDER") or os.getenv("VERCEL"):
    app.config.update(
        SESSION_COOKIE_SAMESITE='None',
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_NAME='__Host-spam-shield-session' if not os.getenv("DEBUG") else 'spam-shield-session'
    )

def get_google_flow():
    """Create a Google OAuth2 flow for web login with dynamic URL detection."""
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError("Google Cloud 'credentials.json' missing from root directory.")

    with open('credentials.json', 'r') as f:
        cred_data = json.load(f)

    cred_section = cred_data.get('installed') or cred_data.get('web')
    
    # Auto-detect the backend URL
    # On Render, we want the https://... url. 
    # request.host_url provides the current server's URL (e.g., https://spam-app.onrender.com/)
    try:
        current_base_url = request.host_url.rstrip('/')
        # Replace http with https for production
        if "onrender.com" in current_base_url:
            current_base_url = current_base_url.replace("http://", "https://")
    except:
        current_base_url = os.getenv("BACKEND_URL", "http://localhost:5000").rstrip('/')
    
    redirect_uri = f"{current_base_url}/api/auth/google/callback"
    
    client_config = {
        'web': {
            'client_id': cred_section['client_id'],
            'client_secret': cred_section['client_secret'],
            'auth_uri': cred_section['auth_uri'],
            'token_uri': cred_section['token_uri'],
            'redirect_uris': [redirect_uri]
        }
    }

    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )


@app.route("/", methods=["GET"])
def api_status():
    """Welcome/Health check route for the Headless Backend."""
    return jsonify({
        "status": "online",
        "service": "Spam Email Detection AI Shield Backend",
        "version": "1.0.0",
        "message": "Backend is active. Please use the Vercel frontend to access the full application.",
        "documentation": "https://github.com/SSbhadoria21/Spam-Email-Detection-App",
        "engine": "Scikit-Learn / Multinomial Naive Bayes"
    })


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
    # Security check: verify state to prevent CSRF
    stored_state = session.pop('oauth_state', None)
    if not stored_state or request.args.get('state') != stored_state:
        return jsonify({"error": "invalid_state", "message": "State mismatch. Potential CSRF detected."}), 400

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
    # Use Vercel URL as default in production
    default_frontend = "https://spam-email-detection-app-xi.vercel.app" if os.getenv("RENDER") else "http://localhost:8080"
    frontend_url = os.getenv("FRONTEND_URL", default_frontend).rstrip('/')
    return redirect(f"{frontend_url}/dashboard")


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
    """
    Simplified Core Gmail Fetch:
    1. Fetch 30 most recent emails from Gmail.
    2. Scan them immediately.
    3. Return ONLY these 30 emails (fixing the count explosion).
    4. Automatically cleanup any old duplicates from history.
    """
    try:
        import hashlib
        service = get_gmail_service()
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'

        # Step 1: Automatic Cleanup (Repair the 47-email pollution)
        # We find and delete all existing legacy 'source=gmail' history for this user once
        if db:
            docs_to_purge = list(db.collection('history')
                               .where("user_email", "==", user_email)
                               .where("Source", "==", "gmail")
                               .stream())
            if len(docs_to_purge) > 30: # Only purge if it looks like the "47 email" bug happened
                batch = db.batch()
                for doc in docs_to_purge:
                    batch.delete(doc.reference)
                batch.commit()
                print(f"Core Reset: Purged {len(docs_to_purge)} polluted history records.")

        # Step 2: Build seen_keys to avoid double-saving identical messages
        seen_keys = set()
        if db:
            docs = db.collection('history').where("user_email", "==", user_email).where("Source", "==", "gmail").stream()
            for doc in docs:
                seen_keys.add(doc.id)

        # Step 3: Fetch 30 most recent messages from Inbox and Spam folders
        # Exclude Drafts to keep the count accurate
        results = service.users().messages().list(userId='me', maxResults=30, q="{label:INBOX label:SPAM} -label:DRAFT").execute()
        messages = results.get('messages', [])

        final_results = []

        for m in messages:
            msg_id = m['id']
            try:
                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                snippet = msg.get('snippet', '').strip()
                
                # Filter out empty messages, drafts, or system placeholders
                # (Fixes the "26 emails instead of 24" issue)
                label_ids = msg.get('labelIds', [])
                if not snippet or 'DRAFT' in label_ids:
                    continue

                internal_date_ms = msg.get('internalDate', str(int(datetime.now().timestamp() * 1000)))
                date_val = datetime.fromtimestamp(int(internal_date_ms)/1000.0).isoformat()
                
                headers = msg.get('payload', {}).get('headers', [])
                sender = "Unknown Sender"
                subject = "(No Subject)"
                for h in headers:
                    if h.get('name', '').lower() == 'from':
                        sender = h.get('value')
                    if h.get('name', '').lower() == 'subject':
                        subject = h.get('value')

                # Core action: scan freshenly OR auto-flag if already in Gmail Spam
                label_ids = msg.get('labelIds', [])
                if 'SPAM' in label_ids:
                    prediction = "SPAM"
                    score = 100.0
                    category = "Gmail Flagged"
                else:
                    prediction, score, category = predict_spam(snippet)

                # Store result in final list for UI
                res_item = {
                    'sender': sender,
                    'subject': subject,
                    'snippet': snippet,
                    'result': prediction,
                    'score': float(score),
                    'category': category,
                    'isSpam': prediction == "SPAM"
                }
                final_results.append(res_item)

                # Background: ONLY save to history if it's a new message
                composite_key = f"{user_email}__{snippet}__{internal_date_ms}"
                key_hash = hashlib.md5(composite_key.encode()).hexdigest()
                
                if db and key_hash not in seen_keys:
                    save_to_history(sender, snippet, prediction, score, 
                                    category=category, source="gmail", 
                                    gmail_id=msg_id, subject=subject, 
                                    date_val=date_val, doc_id=key_hash)
                    seen_keys.add(key_hash)

            except Exception as inner_e:
                print(f"Error processing message {msg_id}: {inner_e}")
                continue

        if not final_results:
            return jsonify({"emails": [], "message": "No emails found in inbox."})

        return jsonify({"emails": final_results})

    except Exception as e:
        return jsonify({"error": f"Gmail Fetch Error: {str(e)}"}), 500

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
            return jsonify({"charts": {"ratio": None, "categories": None}, "message": "No data available."})
            
        # 1. Pie Chart (Spam vs Safe)
        fig1, ax1 = plt.subplots(figsize=(5, 5))
        # Premium Teal/Cyan theme
        colors = ['#F87171', '#14FFEC'] # Red for spam, Cyan for safe
        ax1.pie([spam_count, safe_count], labels=['Spam', 'Safe'], autopct='%1.1f%%', startangle=90, colors=colors, 
                textprops={'color':"#F9FAFB", 'weight':'bold', 'fontsize': 10}, pctdistance=0.85)
        
        # Add a circle at the center to make it a doughnut if preferred
        ax1.axis('equal') 
        fig1.patch.set_facecolor('#030712') # Match dashboard bg
        plt.tight_layout()
        
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png', transparent=True)
        buf1.seek(0)
        chart_ratio = base64.b64encode(buf1.read()).decode('utf-8')
        plt.close(fig1)
        
        # 2. Bar Chart (Categories)
        chart_categories = None
        if categories:
            fig2, ax2 = plt.subplots(figsize=(7, 4))
            cats = list(categories.keys())
            c_vals = list(categories.values())
            ax2.bar(cats, c_vals, color='#14FFEC') # Cyan accent color
            ax2.tick_params(axis='x', colors='#9CA3AF', labelsize=8)
            ax2.tick_params(axis='y', colors='#9CA3AF', labelsize=8)
            ax2.spines['bottom'].set_color('#374151')
            ax2.spines['left'].set_color('#374151')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            plt.xticks(rotation=15, ha='right')
            fig2.patch.set_facecolor('#030712')
            ax2.set_facecolor('#030712')
            
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
            colors = ['#F87171', '#14FFEC']
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
            colors = ['#14FFEC', '#C084FC', '#F59E0B', '#34D399', '#F87171']
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


# --- Serve React SPA (must be last route) ---
@app.route("/", defaults={'path': ''}, strict_slashes=False)
@app.route("/<path:path>", strict_slashes=False)
def serve(path):
    """Catch-all for React Router - serve index.html for SPA routes."""
    # Serve actual static files (JS, CSS, images, favicon)
    if path:
        file_path = os.path.join(DIST_DIR, path)
        if os.path.isfile(file_path):
            return send_from_directory(DIST_DIR, path)
    # Fallback to index.html for all React Router paths
    return send_from_directory(DIST_DIR, 'index.html')


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "1").lower() not in ("0", "false", "no")
    app.run(debug=debug, host="0.0.0.0", port=port)