import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Shield, BarChart3, Eye } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const SettingsPage = () => {
  const [detailedReports, setDetailedReports] = useState(true);
  const { logout } = useAuth();

  const handleClearAll = async () => {
    localStorage.removeItem("spamguard_history");
    localStorage.removeItem("spamguard_user");
    try {
      await fetch("/api/history/clear", { method: "POST" });
      await logout();
    } catch {}
    window.location.href = "/";
  };

  return (
    <div className="p-6 md:p-10 max-w-4xl mx-auto pb-32 font-sans">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="mb-12">
          <h1 className="text-4xl font-black text-foreground mb-2 tracking-tighter uppercase">
            System <span className="text-primary">Settings</span>
          </h1>
          <p className="text-muted-foreground">Manage your application preferences and security protocols</p>
        </div>

        <div className="mt-12 space-y-4">
          <h3 className="text-xl font-bold text-foreground mb-6">System Preferences</h3>
          {[
            { icon: Eye, label: "Detailed Reports", desc: "Show full analysis breakdown", checked: detailedReports, onChange: setDetailedReports },
          ].map((setting) => (
            <div
              key={setting.label}
              className="rounded-xl border border-border bg-card p-5 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 rounded-lg bg-secondary">
                  <setting.icon className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <Label className="text-foreground font-medium">{setting.label}</Label>
                  <p className="text-xs text-muted-foreground">{setting.desc}</p>
                </div>
              </div>
              <Switch checked={setting.checked} onCheckedChange={setting.onChange} />
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 mt-8">
          <h3 className="text-lg font-semibold text-destructive mb-2">Danger Zone</h3>
          <p className="text-sm text-muted-foreground mb-4">Delete all data, scan history, and logout. This action cannot be undone.</p>
          <button
            onClick={handleClearAll}
            className="px-4 py-2 rounded-lg border border-destructive text-destructive text-sm hover:bg-destructive/10 transition-colors"
          >
            Delete All Data & Logout
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default SettingsPage;
