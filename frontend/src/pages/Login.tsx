import { useState } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Shield, Loader2, AlertTriangle, X } from "lucide-react";
import { Button } from "@/components/ui/button";

const GoogleIcon = () => (
  <svg viewBox="0 0 24 24" width="20" height="20" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
      fill="#4285F4"
    />
    <path
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      fill="#34A853"
    />
    <path
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      fill="#FBBC05"
    />
    <path
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      fill="#EA4335"
    />
  </svg>
);

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ title: string; message: string } | null>(null);

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      // Probe the endpoint first — if credentials.json is missing it returns JSON
      const res = await fetch("/api/auth/google/login", { redirect: "manual" });

      // opaqueredirect means the server issued a real 302 → OAuth is configured, follow it
      if (res.type === "opaqueredirect" || res.redirected || res.status === 302) {
        window.location.href = "/api/auth/google/login";
        return;
      }

      const contentType = res.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await res.json();
        if (data.error) {
          let title = "Google Sign-In Unavailable";
          let message = data.message || "An unknown error occurred.";
          if (data.error === "credentials_missing") {
            title = "Setup Required: credentials.json Missing";
            message =
              "The Google OAuth credentials file is not configured on the server.\n\n" +
              "To fix this:\n" +
              "1. Go to Google Cloud Console → APIs & Services → Credentials\n" +
              "2. Create an OAuth 2.0 Client ID (Desktop App)\n" +
              "3. Download the JSON and save it as credentials.json in the project root folder\n" +
              "4. Restart the Flask server (python app.py)";
          } else if (data.error === "credentials_invalid") {
            title = "Invalid credentials.json";
          }
          setError({ title, message });
          setLoading(false);
          return;
        }
      }

      // Non-JSON success → OAuth started fine, follow the redirect
      window.location.href = "/api/auth/google/login";
    } catch {
      // Network error — try direct redirect anyway
      window.location.href = "/api/auth/google/login";
    }
  };

  return (
    <div className="min-h-screen bg-background bg-grid flex items-center justify-center p-6 relative">
      <div className="absolute top-1/3 left-1/3 w-80 h-80 bg-primary/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/3 right-1/3 w-60 h-60 bg-accent/10 rounded-full blur-[100px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md relative z-10"
      >
        <Link to="/" className="flex items-center gap-2 justify-center mb-8">
          <Shield className="h-8 w-8 text-primary" />
          <span className="text-2xl font-bold text-foreground">
            Spam Email <span className="text-primary italic">Detection</span>
          </span>
        </Link>

        <div className="rounded-2xl border border-border bg-card/80 backdrop-blur-xl p-8">
          <h1 className="text-2xl font-bold text-foreground mb-1 text-center">Welcome</h1>
          <p className="text-sm text-muted-foreground mb-6 text-center">
            Sign in with your Google account to continue
          </p>

          {/* Error Banner */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 rounded-xl border border-yellow-500/40 bg-yellow-500/10 p-4 relative"
            >
              <button
                onClick={() => setError(null)}
                className="absolute top-3 right-3 text-yellow-400 hover:text-yellow-200 transition-colors"
                aria-label="Dismiss error"
              >
                <X className="h-4 w-4" />
              </button>
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-400 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-yellow-300 mb-2">{error.title}</p>
                  <pre className="text-xs text-yellow-200/80 whitespace-pre-wrap font-sans leading-relaxed">
                    {error.message}
                  </pre>
                </div>
              </div>
            </motion.div>
          )}

          <Button
            onClick={handleGoogleLogin}
            disabled={loading}
            variant="outline"
            className="w-full py-6 text-base gap-3 border-border hover:border-primary hover:bg-secondary transition-all"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Connecting to Google...
              </>
            ) : (
              <>
                <GoogleIcon />
                Sign in with Google
              </>
            )}
          </Button>

          <div className="mt-6 pt-6 border-t border-border">
            <p className="text-xs text-muted-foreground text-center">
              By signing in, you grant Spam Email Detection App read-only access to your Gmail
              inbox for spam analysis. We never modify or delete your emails.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
