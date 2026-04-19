import { NavLink, useNavigate, useLocation, Link } from "react-router-dom";
import { Shield, Search, History, Settings, User, LogOut, Inbox, BarChart3, ChevronLeft, ChevronRight, Code2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", icon: Shield, label: "Home", end: true },
  { to: "/dashboard", icon: Search, label: "Detect Spam", end: true },
  { to: "/dashboard/inbox", icon: Inbox, label: "Inbox Scanner" },
  { to: "/dashboard/history", icon: History, label: "History" },
  { to: "/dashboard/visualizations", icon: BarChart3, label: "Visualizations" },
  { to: "/dashboard/profile", icon: User, label: "Profile" },
  { to: "/dashboard/settings", icon: Settings, label: "Settings" },
];

interface DashboardSidebarProps {
  onClose?: () => void;
  isCollapsed: boolean;
  setIsCollapsed: (val: boolean) => void;
}

export const DashboardSidebar = ({ onClose, isCollapsed, setIsCollapsed }: DashboardSidebarProps) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <TooltipProvider>
      <div 
        className={cn(
          "h-full flex flex-col bg-background/40 backdrop-blur-xl border-r border-border/40 transition-all duration-300 relative",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        {/* Toggle Arrow */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-20 bg-primary text-primary-foreground h-6 w-6 rounded-full flex items-center justify-center border border-border/50 shadow-lg hover:scale-110 transition-transform z-50 hidden lg:flex"
        >
          {isCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>

        <Link 
          to="/" 
          className={cn("p-6 flex items-center gap-3 hover:opacity-80 transition-opacity", isCollapsed && "justify-center px-0")}
        >
          <img src="/favicon.ico" alt="Logo" className="h-7 w-7 shrink-0" />
          {!isCollapsed && (
            <span className="font-bold text-base text-foreground tracking-tight whitespace-nowrap">
              Spam Email <span className="text-primary italic">Detection</span>
            </span>
          )}
        </Link>

        <nav className="flex-1 px-3 space-y-1 mt-4">
          {links.map((link) => {
            const isActive = link.end 
              ? location.pathname === link.to 
              : location.pathname.startsWith(link.to);

            return (
              <Tooltip key={link.to} delayDuration={0}>
                <TooltipTrigger asChild>
                  <NavLink
                    to={link.to}
                    end={link.end}
                    onClick={onClose}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 rounded-xl text-sm transition-all duration-300 whitespace-nowrap group",
                      isActive
                        ? "bg-primary/10 text-primary font-bold shadow-[0_0_15px_rgba(20,255,236,0.1)]"
                        : "text-muted-foreground hover:bg-white/5 hover:text-foreground hover:translate-x-1",
                      isCollapsed && "justify-center px-0 hover:translate-x-0"
                    )}
                  >
                    <link.icon className={cn("h-5 w-5 shrink-0", "transition-colors")} />
                    {!isCollapsed && <span>{link.label}</span>}
                  </NavLink>
                </TooltipTrigger>
                {isCollapsed && (
                  <TooltipContent side="right" className="bg-popover/90 backdrop-blur-md">
                    {link.label}
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}
        </nav>

        <div className={cn("p-4 border-t border-border/40 space-y-3", isCollapsed && "px-2")}>
          <div className={cn("flex items-center gap-3 px-3", isCollapsed && "justify-center px-0")}>
            {user?.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="w-8 h-8 rounded-full object-cover shrink-0"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-sm font-bold shrink-0">
                {user?.name?.[0]?.toUpperCase() || "U"}
              </div>
            )}
            {!isCollapsed && (
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-foreground truncate">{user?.name || "User"}</div>
                <div className="text-xs text-muted-foreground truncate">{user?.email || ""}</div>
              </div>
            )}
          </div>
          
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <button
                onClick={handleLogout}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-xl text-sm text-destructive hover:bg-destructive/10 w-full transition-all",
                  isCollapsed && "justify-center px-0"
                )}
              >
                <LogOut className="h-5 w-5 shrink-0" />
                {!isCollapsed && <span className="whitespace-nowrap">Log Out</span>}
              </button>
            </TooltipTrigger>
            {isCollapsed && (
              <TooltipContent side="right" className="bg-destructive/90 text-destructive-foreground">
                Log Out
              </TooltipContent>
            )}
          </Tooltip>
        </div>
      </div>
    </TooltipProvider>
  );
};

