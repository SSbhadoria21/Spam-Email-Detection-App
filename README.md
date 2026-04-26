# Spam Email Detection App

This project is a full-stack web application designed to detect spam emails. It uses a machine learning model to classify emails as either spam or safe and provides a modern, interactive dashboard for users to scan, review, and analyze their email history.

## Features

*   **Spam Detection Model:** Utilizes a Naive Bayes classifier trained on a dataset of emails to accurately predict if an email is spam, providing a probability score.
*   **Gmail Integration:** Allows users to log in securely with their Google account and fetch recent emails directly from their inbox for scanning.
*   **Manual Scanning:** Users can manually paste email text to be analyzed instantly.
*   **Spam Categorization:** Identifies specific types of spam, such as "Phishing/Account Verification," "Investment/Crypto Scam," and "Delivery Scam."
*   **Firestore Database:** Stores scan history securely in Firebase Firestore, with per-user data isolation.
*   **Interactive Analytics:** Features a dedicated analytics dashboard with dynamic charts (Pie, Bar, Line, Doughnut) generated via Matplotlib to visualize spam trends.
*   **Modern UI:** Built with React, Vite, Tailwind CSS, and shadcn/ui for a responsive, accessible, and visually appealing interface.

## Tech Stack

### Backend
*   **Python:** The core scripting language.
*   **Flask:** A lightweight WSGI web application framework to serve the API.
*   **scikit-learn:** Used for the TF-IDF vectorization and the Multinomial Naive Bayes machine learning model.
*   **Pandas:** Used for data manipulation during model training.
*   **Firebase Admin SDK:** Used to connect to Firestore for user and history data storage.
*   **Google API Client:** Used to interact with the Gmail API for fetching emails.
*   **Matplotlib:** Generates backend charts for analytics.

### Frontend
*   **React:** A JavaScript library for building user interfaces.
*   **Vite:** A fast build tool that significantly improves the frontend development experience.
*   **Tailwind CSS:** A utility-first CSS framework for rapid UI development.
*   **shadcn/ui & Radix UI:** Pre-built, customizable UI components for a polished look and feel.
*   **React Router:** For handling navigation between the dashboard, scanning, history, and analytics pages.

## Setup Instructions

### Prerequisites
1.  Python 3.x installed.
2.  Node.js and npm (or yarn) installed.

### Backend Setup

1.  Navigate to the project root directory.
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv spam_env
    # Activate on Windows:
    spam_env\Scripts\activate
    # Activate on macOS/Linux:
    source spam_env/bin/activate
    ```
3.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Firebase Credentials:** Obtain a service account key (`firebase_credentials.json`) from your Firebase console and place it in the root directory.
5.  **Google OAuth Credentials:**
    *   Go to the Google Cloud Console.
    *   Create a project and enable the Gmail API.
    *   Configure the OAuth consent screen.
    *   Create OAuth 2.0 Client IDs (Application type: Desktop/Web application).
    *   Download the JSON file and save it as `credentials.json` in the root directory.

### Frontend Setup

1.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
2.  Install the npm dependencies:
    ```bash
    npm install
    ```

## Running the Application

1.  **Start the Backend:** From the project root directory, run the Flask app:
    ```bash
    python app.py
    ```
    The backend will typically start on `http://localhost:5000`.
2.  **Start the Frontend:** In a separate terminal, from the `frontend` directory, start the Vite development server:
    ```bash
    npm run dev
    ```
    The frontend will typically start on `http://localhost:8080` (or `http://localhost:5173`).
3.  Open the frontend URL in your web browser.

## Deployment Notes

*   **Frontend:** The frontend can be deployed to platforms like Vercel or Netlify. Make sure to configure the API URL in your frontend `.env` to point to your live backend.
*   **Backend:** The backend can be deployed to platforms like Render or Heroku. Ensure you provide the necessary environment variables and the `build.txt` (running `pip install -r requirements.txt`) and a start command (e.g., `gunicorn app:app`). Note that Render deployment requires a `requirements.txt` with only standard python dependencies.
## Deployed Link
https://spam-email-detection-app-xi.vercel.app/
