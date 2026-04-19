from flask import Flask, request, jsonify, session, redirect, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

import firebase_admin
from firebase_admin import credentials, firestore, auth

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
app.secret_key = os.getenv("FLASK_SECRET_KEY", "spam_shield_dev_secret_key_99")
CORS(app, supports_credentials=True, origins=["http://localhost:8080", "http://127.0.0.1:8080"])

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
        "Invoice/Billing Scam": [r"invoice", r"billing", r"subscription", r"auto-renew", r"payment received", r"receipt", r"norton", r"mcafee"],
        "SMS/Promotional Spam": [r"freemsg", r"txt", r"std chgs", r"£", r"rcv", r"stop", r"win", r"prize", r"gift card", r"urgent.*action"]
    }
    
    for category, patterns in scam_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                return category
    
    return "General Spam"

def predict_spam(message):
    if not message or not isinstance(message, str):
        message = ""
    
    # Run heuristics first for manual override
    heuri_cat = categorize_spam(message)
    
    msg_vec = vectorizer.transform([message])
    prediction = model.predict(msg_vec)[0]
    probs = model.predict_proba(msg_vec)[0]
    spam_index = list(model.classes_).index("SPAM")
    
    # Always return spam probability as score (high = spam, low = safe)
    spam_score = round(probs[spam_index] * 100, 1)
    
    # HEURISTIC OVERRIDE: If we found a specific scam category, force SPAM result
    if heuri_cat != "General Spam":
        prediction = "SPAM"
        spam_score = max(spam_score, 99.9) # Boost confidence
        category = heuri_cat
    else:
        category = "General Spam" if prediction == "SPAM" else None
        
    return prediction, spam_score, category


def save_to_history(sender, message, result, score, category=None, source="manual", gmail_id=None, subject=None, date_val=None, doc_id=None):
    """Save scan result to Firestore history."""
    if not db:
        print("Firestore not initialized, cannot save history.")
        return
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        doc_data = {
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
            
        history_ref = db.collection('users').document(user_email).collection('history')
        if doc_id:
            history_ref.document(doc_id).set(doc_data)
        else:
            history_ref.add(doc_data)
    except Exception as e:
        print(f"Error saving to Firestore history: {e}")


# --- Gmail API Setup ---
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

def save_user_token(email, creds):
    """Save Google OAuth credentials to Firestore for a specific user."""
    if not db:
        return
    try:
        token_data = json.loads(creds.to_json())
        db.collection('users').document(email).collection('private').document('credentials').set(token_data)
        print(f"Token saved to Firestore for {email}")
    except Exception as e:
        print(f"Error saving token to Firestore: {e}")

def load_user_token(email):
    """Load Google OAuth credentials from Firestore for a specific user."""
    if not db:
        return None
    try:
        doc = db.collection('users').document(email).collection('private').document('credentials').get()
        if doc.exists:
            return Credentials.from_authorized_user_info(doc.to_dict(), SCOPES)
    except Exception as e:
        print(f"Error loading token from Firestore: {e}")
    return None

def get_gmail_service(email=None):
    if not email:
        email = session.get('user', {}).get('email')
    
    if not email:
        raise ValueError("No user email found in session for Gmail service.")

    creds = load_user_token(email)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_user_token(email, creds)
        else:
            # If no token exists, we expect the OAuth flow to handle creation
            # Returning None so the caller can redirect to /api/auth/google/login
            return None
            
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
else:
    # LOCAL DEV: Allow cookies across ports on localhost
    app.config.update(
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True
    )

def get_google_flow():
    """Create a Google OAuth2 flow with hardcoded production URLs to prevent mismatch errors."""
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError("Google Cloud 'credentials.json' missing from root directory.")

    with open('credentials.json', 'r') as f:
        cred_data = json.load(f)

    # Use 'web' credentials for production
    cred_section = cred_data.get('web') or cred_data.get('installed')
    
    # PRODUCTION FIX: Hardcode the Vercel URL as the primary redirect
    if os.getenv("RENDER"):
        current_base_url = "https://spam-email-detection-app-xi.vercel.app"
    else:
        # LOCAL DEV FIX: Google Console is sensitive to 'localhost' vs '127.0.0.1'.
        # We force 'localhost:5000' to match the standard configuration in credentials.json.
        current_base_url = "http://localhost:5000"
    
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
        prompt='select_account consent'
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
    
    # Credentials are saved below after user info is fetched
    
    # Get user info from Google
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    
    try:
        google_creds = flow.credentials
        user_info_service = build('oauth2', 'v2', credentials=google_creds)
        user_info = user_info_service.userinfo().get().execute()
        
        session['user'] = {
            'email': user_info.get('email', ''),
            'name': user_info.get('name', user_info.get('email', '').split('@')[0]),
            'picture': user_info.get('picture', '')
        }
        
        # Save token and profile to firestore
        if db:
            try:
                user_email_key = session['user']['email']
                if user_email_key:
                    db.collection('users').document(user_email_key).set(session['user'], merge=True)
                    # Save the OAuth credentials specifically to this user's private collection
                    save_user_token(user_email_key, google_creds)
                    
                    # Sync with Firebase Authentication Dashboard
                    try:
                        try:
                            # Check if user already exists in Firebase Auth
                            auth_user = auth.get_user_by_email(user_email_key)
                            # Update existing user info
                            auth.update_user(
                                auth_user.uid,
                                display_name=session['user']['name'],
                                photo_url=session['user']['picture']
                            )
                            print(f"Firebase Auth: Updated existing user {user_email_key}")
                        except auth.UserNotFoundError:
                            # Create new user in Firebase Auth if they don't exist
                            auth.create_user(
                                email=user_email_key,
                                display_name=session['user']['name'],
                                photo_url=session['user']['picture'],
                                email_verified=True
                            )
                            print(f"Firebase Auth: Created new user {user_email_key}")
                    except Exception as auth_err:
                        print(f"Background: Syncing with Firebase Auth Dashboard failed (this doesn't block the app): {auth_err}")
            except Exception as e:
                print(f"Error saving user profile/token to Firestore: {e}")
                
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
        print(f"Auth Check: User {user.get('email')} is authenticated.")
        return jsonify({"authenticated": True, "user": user})
    print("Auth Check: No user session found.")
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
    
    # Manual Input scans are now stateless (not saved to history as per user request)
    # save_to_history("Manual Input", email_text, result, score, category=category, source="manual")
    
    return jsonify({
        "result": result,
        "score": score,
        "category": category,
        "isSpam": result == "SPAM"
    })


@app.route("/api/fetch-gmail", methods=["POST"])
def api_fetch_gmail():
    """Fetch 30 most recent emails from Gmail and scan them."""
    try:
        user_email = session.get('user', {}).get('email')
        if not user_email:
            return jsonify({"error": "Unauthorized"}), 401

        service = get_gmail_service(user_email)
        if not service:
            return jsonify({"error": "gmail_auth_required", "message": "Please re-login to authorize Gmail access."}), 401

        # Build seen_keys to avoid double-saving identical messages
        seen_keys = set()
        if db:
            docs = db.collection('users').document(user_email).collection('history').where("Source", "==", "gmail").stream()
            for doc in docs:
                seen_keys.add(doc.id)

        results = service.users().messages().list(userId='me', maxResults=30, q="{label:INBOX label:SPAM} -label:DRAFT").execute()
        messages = results.get('messages', [])
        final_results = []

        for m in messages:
            msg_id = m['id']
            try:
                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                snippet = msg.get('snippet', '').strip()
                label_ids = msg.get('labelIds', [])
                if not snippet or 'DRAFT' in label_ids:
                    continue

                internal_date_ms = msg.get('internalDate', str(int(datetime.now().timestamp() * 1000)))
                date_val = datetime.fromtimestamp(int(internal_date_ms)/1000.0).isoformat()
                
                headers = msg.get('payload', {}).get('headers', [])
                sender, subject = "Unknown Sender", "(No Subject)"
                for h in headers:
                    if h.get('name', '').lower() == 'from': sender = h.get('value')
                    if h.get('name', '').lower() == 'subject': subject = h.get('value')

                if 'SPAM' in label_ids:
                    prediction, score, category = "SPAM", 100.0, "Gmail Flagged"
                else:
                    prediction, score, category = predict_spam(snippet)

                final_results.append({
                    'sender': sender, 'subject': subject, 'snippet': snippet,
                    'result': prediction, 'score': float(score), 'category': category, 'isSpam': prediction == "SPAM"
                })

                composite_key = f"{user_email}__{snippet}__{internal_date_ms}"
                key_hash = hashlib.md5(composite_key.encode()).hexdigest()
                
                if db and key_hash not in seen_keys:
                    save_to_history(sender, snippet, prediction, score, category=category, source="gmail", 
                                    gmail_id=msg_id, subject=subject, date_val=date_val, doc_id=key_hash)
                    seen_keys.add(key_hash)
            except Exception as inner_e:
                print(f"Error processing message {msg_id}: {inner_e}")
                continue

        return jsonify({"emails": final_results})
    except Exception as e:
        return jsonify({"error": f"Gmail Fetch Error: {str(e)}"}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return scan history from Firestore."""
    if not db:
        return jsonify({"history": [], "error": "Firestore not initialized."})
    
    try:
        # Optimization: Sort and limit on server side (requires Firestore index)
        # If index doesn't exist, we fallback to client-side sort but still stream for efficiency
        history_query = db.collection('users').document(user_email).collection('history')
        
        try:
            docs = history_query.order_by('Date', direction=firestore.Query.DESCENDING).limit(200).stream()
        except:
            # Fallback for if index is missing in development
            docs = history_query.stream()
            
        history = []
        for doc in docs:
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
        docs = db.collection('users').document(user_email).collection('history').get()
        
        if docs:
            batch = db.batch()
            for doc in docs:
                batch.delete(doc.reference)
            batch.commit()
            
        return jsonify({"status": "cleared"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/history/delete/<doc_id>", methods=["DELETE"])
def api_delete_history_item(doc_id):
    """Delete a specific history shard by ID."""
    if not db:
        return jsonify({"status": "error", "message": "Firestore not initialized."}), 500
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        doc_ref = db.collection('users').document(user_email).collection('history').document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return jsonify({"status": "error", "message": "Record not found."}), 404
            
        doc_ref.delete()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/analytics/charts", methods=["GET"])
def api_analytics_charts():
    """Generate Matplotlib charts for user analytics."""
    if not db:
        return jsonify({"error": "Firestore not initialized."})
        
    try:
        user_email = session.get('user', {}).get('email', 'anonymous@local') if session else 'anonymous@local'
        # Optimization: Only select the fields needed for the charts
        docs = db.collection('users').document(user_email).collection('history').select(['Result', 'Category']).stream()
        
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
        # Vibrant Colorful structures
        colors = ['#EF4444', '#10B981'] # Red for spam, Emerald for safe
        patches, texts, pcts = ax1.pie([spam_count, safe_count], labels=['Spam', 'Safe'], autopct='%1.1f%%', startangle=90, colors=colors, 
                                     textprops={'color':"black", 'weight':'bold', 'fontsize': 10}, pctdistance=0.75)
        
        # Style percentages to be visible on colorful wedges
        plt.setp(pcts, color='black')
        
        ax1.axis('equal') 
        fig1.patch.set_facecolor('white') 
        ax1.set_facecolor('white')
        ax1.legend(loc="upper right", fontsize=8)
        plt.tight_layout()
        
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png') # background now solid white
        buf1.seek(0)
        chart_ratio = base64.b64encode(buf1.read()).decode('utf-8')
        plt.close(fig1)
        
        # 2. Bar Chart (Categories)
        chart_categories = None
        if categories:
            fig2, ax2 = plt.subplots(figsize=(7, 4))
            cats = list(categories.keys())
            c_vals = list(categories.values())
            # Use colorful palette for bars
            bar_colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
            bars = ax2.bar(cats, c_vals, color=bar_colors[:len(cats)])
            
            ax2.tick_params(axis='x', colors='black', labelsize=8)
            ax2.tick_params(axis='y', colors='black', labelsize=8)
            ax2.spines['bottom'].set_color('black')
            ax2.spines['left'].set_color('black')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            
            plt.xticks(rotation=15, ha='right')
            fig2.patch.set_facecolor('white')
            ax2.set_facecolor('white')
            ax2.legend(bars, cats, loc="upper right", fontsize=8)
            
            plt.tight_layout()
            buf2 = io.BytesIO()
            plt.savefig(buf2, format='png')
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
        # Optimization: Only load the fields relevant to analytics
        docs = db.collection('users').document(user_email).collection('history').select(['Result', 'Category', 'Date']).stream()
        
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
            patches, texts, pcts = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)], textprops={'color':"black"}, pctdistance=0.75)
            plt.setp(pcts, color='black', weight='bold') # Black text on colored wedges
            ax.axis('equal')
            ax.legend(loc="upper right", bbox_to_anchor=(1, 1), fontsize=8)
        elif chart_type == "doughnut":
            patches, texts, pcts = ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)], textprops={'color':"black"}, wedgeprops=dict(width=0.4, edgecolor='none'), pctdistance=0.75)
            plt.setp(pcts, color='black', weight='bold')
            ax.axis('equal')
            ax.legend(loc="upper right", bbox_to_anchor=(1, 1), fontsize=8)
        elif chart_type == "bar":
            cc = colors if len(colors) >= len(labels) else (colors*(len(labels)//len(colors)+1))[:len(labels)]
            bars = ax.bar(labels, values, color=cc)
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='black')
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(rotation=15, ha='right')
            ax.legend(bars, labels, loc="upper right", fontsize=8)
        elif chart_type == "line":
            line, = ax.plot(labels, values, marker='o', color='#3B82F6', linewidth=2, markersize=8, label=metric.capitalize())
            ax.tick_params(axis='x', colors='black')
            ax.tick_params(axis='y', colors='black')
            ax.spines['bottom'].set_color('black')
            ax.spines['left'].set_color('black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.xticks(rotation=45, ha='right')
            ax.grid(color='#E5E7EB', linestyle='-', linewidth=0.5, alpha=0.5)
            ax.legend(loc="upper right", fontsize=8)

        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
            
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png') # transparency removed to keep white background
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