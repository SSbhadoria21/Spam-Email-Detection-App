import { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Menu } from "lucide-react";
import { cn } from "@/lib/utils";

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const saved = localStorage.getItem("sidebar_collapsed");
    return saved ? JSON.parse(saved) : false;
  });

  useEffect(() => {
    localStorage.setItem("sidebar_collapsed", JSON.stringify(isCollapsed));
  }, [isCollapsed]);

  return (
    <div className="h-screen bg-[radial-gradient(circle_at_50%_0%,rgba(17,24,39,1)_0%,rgba(3,7,18,1)_100%)] flex relative overflow-hidden">
      {/* Decorative Blur Elements */}
      <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-accent/5 rounded-full blur-[100px] translate-x-1/4 translate-y-1/4 pointer-events-none" />

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-background/40 backdrop-blur-md z-40 lg:hidden transition-all duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Fixed on desktop */}
      <div
        className={cn(
          "fixed inset-y-0 left-0 z-50 transform transition-all duration-300 lg:translate-x-0 bg-background/40 backdrop-blur-xl border-r border-border/10",
          isCollapsed ? "w-20" : "w-64",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <DashboardSidebar 
          onClose={() => setSidebarOpen(false)} 
          isCollapsed={isCollapsed}
          setIsCollapsed={setIsCollapsed}
        />
      </div>

      {/* Main Content Area */}
      <div 
        className={cn(
          "flex-1 flex flex-col h-screen transition-all duration-300 overflow-hidden",
          isCollapsed ? "lg:ml-20" : "lg:ml-64"
        )}
      >
        {/* Unified Navbar */}
        <div className="flex-shrink-0 z-30 w-full flex items-center">
          {/* Mobile toggle button (placed inside navbar for dash only) */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden ml-6 text-muted-foreground hover:text-foreground transition-colors"
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex-1">
            <Navbar />
          </div>
        </div>

        <main className="flex-1 overflow-y-auto px-6 py-8 flex flex-col min-w-0">
          <div className="flex-1">
            <Outlet />
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
