import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Send, AlertTriangle, CheckCircle, Search, Info, Loader2, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ThreeDCard } from "@/components/landing/ThreeDCard";

interface AnalysisResult {
  isSpam: boolean;
  score: number;
  result: string;
  category?: string;
}

const SpamDetector = () => {
  const [emailText, setEmailText] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  const handleAnalyze = async () => {
    if (!emailText.trim()) return;
    setAnalyzing(true);
    setResult(null);

    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email_text: emailText }),
      });

      if (!response.ok) {
        throw new Error("Analysis failed");
      }

      const data = await response.json();

      setResult({
        isSpam: data.isSpam,
        score: data.score,
        result: data.result,
        category: data.category,
      });
    } catch (error) {
      console.error("Error analyzing email:", error);
      setResult({
        isSpam: false,
        score: 0,
        result: "ERROR",
      });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto pb-32">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-4xl font-black text-foreground mb-2 tracking-tighter uppercase">
          Algorithmic <span className="text-primary tracking-tight">Interceptor</span>
        </h1>
        <p className="text-muted-foreground font-medium mb-10">Real-time spam analysis powered by Bayes-Probabilistic modeling</p>

        <ThreeDCard>
          <div className="rounded-3xl border border-border/40 bg-card/40 backdrop-blur-xl p-8 md:p-12 shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-primary/5 rounded-full blur-[100px] pointer-events-none group-hover:bg-primary/10 transition-colors duration-700" />
            
            <div className="mb-8 flex items-center gap-5 relative z-10">
              <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20 shadow-lg shadow-primary/5">
                <Search className="h-7 w-7 text-primary" />
              </div>
              <div>
                <h3 className="text-2xl font-black text-foreground tracking-tight">Data Entry</h3>
                <p className="text-sm text-muted-foreground font-medium">Inject raw email payload for deep scanning</p>
              </div>
            </div>

            <div className="space-y-6 relative z-10">
              <Textarea
                placeholder="Paste the email content here..."
                className="min-h-[250px] bg-background/30 border-border/40 focus:border-primary/50 text-foreground resize-none text-md p-8 rounded-[2rem] transition-all backdrop-blur-md shadow-inner placeholder:text-muted-foreground/40"
                value={emailText}
                onChange={(e) => setEmailText(e.target.value)}
              />
              <Button
                size="lg"
                onClick={handleAnalyze}
                disabled={analyzing || !emailText.trim()}
                className="w-full h-16 bg-primary text-primary-foreground hover:opacity-90 font-black text-xl rounded-2xl shadow-2xl shadow-primary/30 gap-3 relative overflow-hidden group/btn"
              >
                {analyzing ? (
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Scanning Content...
                  </div>
                ) : (
                  <>
                    Execute Scan
                    <Send className="h-6 w-6 group-hover/btn:translate-x-2 group-hover/btn:-translate-y-2 transition-transform duration-300" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </ThreeDCard>

        {/* Result */}
        <AnimatePresence>
          {result && result.result !== "ERROR" && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 30 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="mt-12"
            >
              <ThreeDCard>
                <div className={`rounded-[2.5rem] border p-10 md:p-12 shadow-2xl relative overflow-hidden ${
                  result.isSpam 
                    ? "bg-destructive/5 border-destructive/20" 
                    : "bg-primary/5 border-primary/20"
                }`}>
                  <div className="flex flex-col md:flex-row items-center gap-10 relative z-10 mb-10">
                    <div className={`p-8 rounded-full shadow-2xl ${
                      result.isSpam ? "bg-destructive/20 shadow-destructive/20" : "bg-primary/20 shadow-primary/20"
                    }`}>
                      {result.isSpam ? (
                        <AlertTriangle className="h-14 w-14 text-destructive" />
                      ) : (
                        <CheckCircle className="h-14 w-14 text-primary" />
                      )}
                    </div>
                    
                    <div className="flex-1 text-center md:text-left">
                      <h2 className="text-4xl font-black mb-2 tracking-tight uppercase">
                        {result.isSpam ? "Threat Detected" : "Verified Payload"}
                      </h2>
                      <p className="text-muted-foreground mb-6 font-bold text-lg">
                        System confidence: <span className="text-foreground">{result.score}%</span>
                      </p>
                      
                      {result.isSpam && result.category && (
                        <div className="inline-flex items-center gap-3 px-6 py-2.5 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive text-sm font-black uppercase tracking-widest">
                          <Info className="h-4 w-4" />
                          Shard: {result.category}
                        </div>
                      )}
                    </div>

                    <div className="md:border-l border-white/5 md:pl-10 flex flex-col items-center justify-center min-w-[180px]">
                      <span className="text-xs font-black text-muted-foreground uppercase tracking-[0.3em] mb-2">Risk Factor</span>
                      <div className={`text-6xl font-black tracking-tighter ${
                        result.isSpam ? "text-destructive" : "text-primary"
                      }`}>
                        {result.score}
                      </div>
                    </div>
                  </div>

                  {/* Detail Panel */}
                  <div className="grid md:grid-cols-2 gap-6 relative z-10 pt-10 border-t border-white/5">
                    <div className="rounded-3xl bg-background/40 p-6 border border-white/5">
                       <div className="flex items-center gap-3 mb-4">
                          <BarChart3 className="h-5 w-5 text-primary" />
                          <span className="text-xs font-black uppercase tracking-widest text-foreground">Analysis Log</span>
                       </div>
                       <ul className="space-y-3">
                          {[
                            `Classification: ${result.result}`,
                            `Probability: ${result.score}%`,
                            `Category: ${result.category || "General"}`,
                            "Audit: Record persisted to secure history"
                          ].map((log, i) => (
                            <li key={i} className="text-xs text-muted-foreground flex items-center gap-2">
                               <div className="h-1 w-1 rounded-full bg-primary" />
                               {log}
                            </li>
                          ))}
                       </ul>
                    </div>
                    <div className="rounded-3xl bg-background/40 p-6 border border-white/5">
                       <div className="flex items-center gap-3 mb-4">
                          <Shield className="h-5 w-5 text-accent" />
                          <span className="text-xs font-black uppercase tracking-widest text-foreground">Protocol Note</span>
                       </div>
                       <p className="text-xs text-muted-foreground leading-relaxed italic">
                         "Analysis performed using TF-IDF vector shards and a Multinomial Naive Bayes classification engine. 
                         Confidence ratings are based on high-dimensional word frequency heuristics."
                       </p>
                    </div>
                  </div>
                </div>
              </ThreeDCard>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error state */}
        <AnimatePresence>
          {result && result.result === "ERROR" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mt-12 rounded-[2rem] border border-destructive/20 bg-destructive/5 p-12 text-center"
            >
              <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h3 className="text-xl font-black text-foreground mb-2 uppercase tracking-tight">Sync Error</h3>
              <p className="text-muted-foreground">The analysis engine is unresponsive. Ensure the Flask backend is active on port 5000.</p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default SpamDetector;
