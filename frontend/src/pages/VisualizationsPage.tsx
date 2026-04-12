import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { BarChart3, Download, Image as ImageIcon, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Link } from "react-router-dom";

const METRICS = [
  { id: "ratio", label: "Spam vs Safe Ratio" },
  { id: "categories", label: "Category Distribution" },
  { id: "timeline", label: "Timeline Activity" }
];

const CHART_TYPES = [
  { id: "pie", label: "Pie Chart" },
  { id: "doughnut", label: "Doughnut Chart" },
  { id: "bar", label: "Bar Chart" },
  { id: "line", label: "Line Chart" }
];

const VisualizationsPage = () => {
  const [metric, setMetric] = useState("ratio");
  const [chartType, setChartType] = useState("doughnut");
  const [chartImage, setChartImage] = useState<string | null>(null);
  const [isEmpty, setIsEmpty] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChart();
  }, [metric, chartType]);

  const fetchChart = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/analytics/custom?metric=${metric}&type=${chartType}`);
      const data = await res.json();
      if (data.empty) {
        setIsEmpty(true);
        setChartImage(null);
      } else if (data.chart) {
        setIsEmpty(false);
        setChartImage(data.chart);
      }
    } catch (e) {
      console.error("Failed to fetch chart", e);
    } finally {
      setLoading(false);
    }
  };

  const downloadImage = () => {
    if (!chartImage) return;
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${chartImage}`;
    link.download = `spamguard_visualization_${metric}_${chartType}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6 md:p-10 max-w-5xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-2">
          <span className="text-gradient-accent">Visualizations</span>
        </h1>
        <p className="text-muted-foreground mb-8">Custom data charts powered by Matplotlib</p>

        {isEmpty ? (
          <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-lg p-12 text-center shadow-xl">
             <Search className="h-16 w-16 text-muted-foreground/50 mx-auto mb-4" />
             <h3 className="text-2xl font-bold text-foreground mb-2">No Visualizations Available</h3>
             <p className="text-muted-foreground mb-6">You haven't scanned any emails yet. Scan your inbox to generate insights!</p>
             <Link to="/scanner">
               <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                 Go to Inbox Scanner
               </Button>
             </Link>
          </div>
        ) : (
          <div className="grid lg:grid-cols-4 gap-6">
            {/* Controls Sidebar */}
            <div className="lg:col-span-1 space-y-6 rounded-2xl border border-border bg-card/60 backdrop-blur-lg p-6 shadow-xl h-fit">
              <div>
                <Label className="text-sm font-bold text-foreground mb-3 block uppercase tracking-wider">Metrics</Label>
                <div className="space-y-2">
                  {METRICS.map(m => (
                    <button
                      key={m.id}
                      onClick={() => setMetric(m.id)}
                      className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition-all duration-200 border ${metric === m.id ? 'bg-primary/20 border-primary text-primary font-medium shadow-[0_0_10px_rgba(45,212,191,0.2)]' : 'bg-transparent border-transparent text-muted-foreground hover:bg-secondary/50'}`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="h-px bg-border w-full"></div>

              <div>
                <Label className="text-sm font-bold text-foreground mb-3 block uppercase tracking-wider">Chart Style</Label>
                <div className="space-y-2">
                  {CHART_TYPES.map(c => (
                    <button
                      key={c.id}
                      onClick={() => setChartType(c.id)}
                      className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition-all duration-200 border ${chartType === c.id ? 'bg-accent/20 border-accent text-accent font-medium shadow-[0_0_10px_rgba(192,132,252,0.2)]' : 'bg-transparent border-transparent text-muted-foreground hover:bg-secondary/50'}`}
                    >
                      {c.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Chart Viewer */}
            <div className="lg:col-span-3 rounded-2xl border border-border bg-card/80 backdrop-blur-xl p-8 shadow-2xl relative overflow-hidden flex flex-col items-center justify-center min-h-[400px]">
              <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-accent/10 rounded-full blur-3xl pointer-events-none"></div>
              
              <div className="w-full flex justify-between items-center mb-6 relative z-10">
                <h3 className="text-xl font-bold text-foreground flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-accent" />
                  Generated Result
                </h3>
                {chartImage && (
                  <Button variant="outline" onClick={downloadImage} className="border-border gap-2 hover:bg-primary/10 hover:text-primary hover:border-primary/50 transition-colors">
                    <Download className="h-4 w-4" />
                    Download PNG
                  </Button>
                )}
              </div>

              <div className="w-full flex-1 flex items-center justify-center relative z-10 bg-background/40 rounded-xl border border-border/50 p-6">
                {loading ? (
                  <div className="flex flex-col items-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mb-4"></div>
                    <p className="text-sm text-muted-foreground animate-pulse">Rendering Matplotlib Chart...</p>
                  </div>
                ) : chartImage ? (
                  <img src={`data:image/png;base64,${chartImage}`} alt="Custom Chart" className="w-full max-w-[600px] object-contain drop-shadow-2xl hover:scale-[1.02] transition-transform duration-500 ease-out" />
                ) : (
                  <div className="text-center text-muted-foreground">
                    <ImageIcon className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p>Failed to load image</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default VisualizationsPage;
