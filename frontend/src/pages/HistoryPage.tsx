import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { History as HistoryIcon, Trash2, AlertTriangle, CheckCircle, RefreshCw, Inbox, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

interface HistoryItem {
  date: string;
  sender: string;
  message: string;
  result: string;
  score: number;
  source: string;
  isSpam: boolean;
  category?: string;
}

const HistoryPage = () => {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const categorizedSpam = useMemo(() => {
    const spams = history.filter((h) => h.isSpam);
    const grouped: Record<string, HistoryItem[]> = {};
    spams.forEach((spam) => {
      const cat = spam.category && spam.category !== "N/A" ? spam.category : "General Spam";
      if (!grouped[cat]) grouped[cat] = [];
      grouped[cat].push(spam);
    });
    return grouped;
  }, [history]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/history");
      const data = await res.json();
      setHistory(data.history || []);
    } catch {
      setHistory([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const clearHistory = async () => {
    await fetch("/api/history/clear", { method: "POST" });
    setHistory([]);
  };

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-2">
              <span className="text-gradient-primary">Detection</span> History
            </h1>
            <p className="text-muted-foreground">All scanned emails stored in CSV</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={fetchHistory} className="border-border gap-2">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            {history.length > 0 && (
              <Button variant="outline" onClick={clearHistory} className="border-destructive/30 text-destructive hover:bg-destructive/10 gap-2">
                <Trash2 className="h-4 w-4" />
                Clear
              </Button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="rounded-2xl border border-border bg-card p-12 text-center">
            <RefreshCw className="h-12 w-12 text-muted-foreground mx-auto mb-4 animate-spin" />
            <p className="text-muted-foreground">Loading scan history...</p>
          </div>
        ) : history.length === 0 ? (
          <div className="rounded-2xl border border-border bg-card p-12 text-center">
            <HistoryIcon className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No detection history yet</p>
            <p className="text-xs text-muted-foreground mt-1">Analyze some emails to see results here</p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between mb-2 text-sm text-muted-foreground">
              <span>{history.length} scan{history.length !== 1 ? "s" : ""} recorded</span>
              <span className="text-destructive font-medium">
                {history.filter((h) => h.isSpam).length} spam detected
              </span>
            </div>

            {Object.keys(categorizedSpam).length > 0 && (
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-foreground mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  Categorized Spam History
                </h3>
                <div className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
                  <Accordion type="single" collapsible className="w-full">
                    {Object.entries(categorizedSpam).map(([category, catItems], idx) => (
                      <AccordionItem key={category} value={`history-${idx}`} className={idx === Object.keys(categorizedSpam).length - 1 ? "border-b-0" : ""}>
                        <AccordionTrigger className="px-4 py-3 hover:bg-muted/50 transition-colors">
                          <div className="flex items-center justify-between w-full pr-4">
                            <span className="font-medium text-destructive">{category}</span>
                            <span className="text-xs bg-destructive/10 text-destructive px-2 py-1 rounded-full">
                              {catItems.length}
                            </span>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="bg-muted/20 p-0 border-t">
                          <div className="max-h-[400px] overflow-y-auto p-4 flex flex-col gap-3">
                            {catItems.map((item, idx2) => (
                              <div key={`${item.date}-${idx2}`} className="rounded-lg border border-border bg-background p-3 flex flex-col gap-1 transition-all hover:border-destructive/30">
                                <div className="flex justify-between items-start gap-2">
                                  <span className="font-medium text-sm text-foreground truncate">{item.sender}</span>
                                  <div className="text-right">
                                    <div className="text-xs text-destructive font-bold">{item.score}%</div>
                                    <div className="text-[10px] text-muted-foreground mt-0.5">{new Date(item.date).toLocaleDateString()}</div>
                                  </div>
                                </div>
                                <div className="text-xs text-muted-foreground truncate">{item.message}</div>
                              </div>
                            ))}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              </div>
            )}

            <h3 className="text-lg font-semibold text-foreground mb-1 mt-4">All Scan History</h3>
            
            <div className="flex flex-col gap-3">
              {history.map((item, i) => (
              <motion.div
                key={`${item.date}-${i}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.03 }}
                className={`rounded-xl border p-4 flex items-start gap-4 ${
                  item.isSpam ? "border-destructive/30 bg-destructive/5" : "border-border bg-card"
                }`}
              >
                <div className={`p-2 rounded-lg flex-shrink-0 ${item.isSpam ? "bg-destructive/20" : "bg-success/20"}`}>
                  {item.isSpam ? (
                    <AlertTriangle className="h-4 w-4 text-destructive" />
                  ) : (
                    <CheckCircle className="h-4 w-4 text-success" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-foreground truncate">{item.sender}</span>
                    <span className="inline-flex items-center gap-1 text-xs text-muted-foreground px-2 py-0.5 rounded-full bg-secondary">
                      {item.source === "gmail" ? (
                        <><Inbox className="h-3 w-3" /> Gmail</>
                      ) : (
                        <><Mail className="h-3 w-3" /> Manual</>
                      )}
                    </span>
                  </div>
                  <p className="text-sm text-foreground truncate mt-1">{item.message}</p>
                  <p className="text-xs text-muted-foreground mt-1 flex items-center gap-2">
                    {new Date(item.date).toLocaleString()} • {item.result} • Spam Score: {item.score}%
                    {item.isSpam && item.category && item.category !== "General Spam" && item.category !== "N/A" && (
                      <span className="inline-block text-[10px] px-1.5 py-0.5 rounded bg-destructive/20 text-destructive border border-destructive/30 uppercase tracking-widest whitespace-nowrap">
                        {item.category}
                      </span>
                    )}
                  </p>
                </div>
                <div className={`text-lg font-bold flex-shrink-0 ${
                  item.score >= 70 ? "text-destructive" : item.score >= 40 ? "text-warning" : "text-success"
                }`}>
                  {item.score}
                </div>
              </motion.div>
            ))}
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default HistoryPage;
