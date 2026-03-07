from flask import Flask, render_template, request
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)

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

def predict_spam(message):
    if not message or not isinstance(message, str):
        message = ""
    msg_vec = vectorizer.transform([message])
    prediction = model.predict(msg_vec)[0]
    probs = model.predict_proba(msg_vec)[0]
    spam_index = list(model.classes_).index("SPAM")
    ham_index = list(model.classes_).index("HAM")
    
    if prediction == "SPAM":
        score = round(probs[spam_index] * 100, 1)
    else:
        score = round(probs[ham_index] * 100, 1)
        
    return prediction, f"{score}%"


# --- Gmail API Setup ---
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
            result, score = predict_spam(email_text)
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
                    
            # Handle CSV append logic
            csv_path = 'fetched_emails.csv'
            new_df = pd.DataFrame(new_emails)
            
            if os.path.exists(csv_path):
                existing_df = pd.read_csv(csv_path)
                combined_df = pd.concat([new_df, existing_df], ignore_index=True)
                # Drop duplicates to prevent redundant logging
                combined_df = combined_df.drop_duplicates(subset=['Message'], keep='first')
            else:
                combined_df = new_df
                
            combined_df.to_csv(csv_path, index=False)
            
            # Read from the combined dataframe and predict
            for index, row in combined_df.iterrows():
                sender = row['Sender']
                snippet = str(row['Message']) if pd.notna(row['Message']) else ""
                
                prediction, score = predict_spam(snippet)
                
                emails_data.append({
                    'sender': sender,
                    'snippet': snippet,
                    'result': prediction,
                    'score': score
                })
            
    except Exception as e:
        error = f"Gmail Fetch Error: {str(e)}"
        
    return render_template("index.html", emails=emails_data, error=error)


if __name__ == "__main__":
   app.run(debug=True, host="0.0.0.0", port=5000)