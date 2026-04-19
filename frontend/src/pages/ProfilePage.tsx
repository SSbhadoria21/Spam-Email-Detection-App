import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { User, Shield, BarChart3 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "react-router-dom";

const ProfilePage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total: 0, spam: 0 });

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const hRes = await fetch("/api/history");
        const hData = await hRes.json();
        if (hData.history) {
           setStats({
              total: hData.history.length,
              spam: hData.history.filter((h: any) => h.isSpam).length
           });
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="grid md:grid-cols-2 gap-6">
        
        {/* Profile Card */}
        <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-lg p-8 shadow-xl">
          <h1 className="text-2xl font-bold text-foreground mb-6">
            <span className="text-gradient-accent">Account details</span>
          </h1>
          <div className="flex items-center gap-4 mb-8">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex flex-shrink-0 items-center justify-center text-primary text-2xl font-bold shadow-[0_0_15px_rgba(45,212,191,0.2)] overflow-hidden">
               {user?.picture ? (
                 <img src={user.picture} alt={user.name} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
               ) : (
                 user?.name?.[0]?.toUpperCase() || "U"
               )}
            </div>
            <div className="overflow-hidden">
              <h2 className="text-xl font-bold text-foreground truncate">{user?.name || "User"}</h2>
              <p className="text-sm text-muted-foreground truncate">{user?.email || "user@example.com"}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <Label className="text-foreground">Full Name</Label>
              <Input defaultValue={user?.name || ""} className="mt-1 bg-secondary/50 border-border" />
            </div>
            <div>
              <Label className="text-foreground">Email</Label>
              <Input defaultValue={user?.email || ""} className="mt-1 bg-secondary/50 border-border" />
            </div>
          </div>
        </div>

        {/* Stats Card */}
        <div className="rounded-2xl border border-border bg-card/60 backdrop-blur-lg p-8 shadow-xl flex flex-col justify-center">
          <h3 className="text-xl font-bold text-foreground mb-6 flex items-center gap-2">
            <Shield className="h-6 w-6 text-primary" />
            Fast Stats
          </h3>
          <div className="grid grid-cols-2 gap-4 text-center">
            {[
              { label: "Emails Scanned", value: stats.total },
              { label: "Spam Found", value: stats.spam },
            ].map((stat) => (
              <div key={stat.label} className="rounded-xl bg-secondary/40 border border-border/50 p-6 shadow-inner hover:scale-105 transition-transform duration-300">
                <div className="text-4xl font-black text-gradient-primary mb-2">{stat.value}</div>
                <div className="text-sm font-medium text-muted-foreground uppercase tracking-wider">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Visualizations Redirect Section */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <div className="rounded-2xl border border-border bg-card/80 backdrop-blur-xl p-8 shadow-2xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-accent/10 rounded-full blur-3xl pointer-events-none"></div>
          
          <div>
            <h3 className="text-2xl font-bold text-foreground mb-2 flex items-center gap-3 relative z-10">
              <BarChart3 className="h-7 w-7 text-accent" />
              Advanced Visual Insights
            </h3>
            <p className="text-muted-foreground relative z-10 max-w-md">
              Dive deeper into your spam patterns with highly customizable, interactive dashboards powered by Matplotlib.
            </p>
          </div>

          <Link to="/dashboard/visualizations" className="relative z-10">
             <Button size="lg" className="bg-accent hover:bg-accent/90 text-accent-foreground font-bold shadow-lg shadow-accent/20">
               Open Custom Visualizations
             </Button>
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default ProfilePage;
