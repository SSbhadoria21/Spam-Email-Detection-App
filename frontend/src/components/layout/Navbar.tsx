import { Link } from "react-router-dom";
import { Search, Code2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";

export const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <nav className="w-full px-6 py-4 border-b border-border/10 bg-background/60 backdrop-blur-xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6 flex-1">
          <div className="relative w-full max-w-sm hidden lg:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search scans, history..."
              className="w-full bg-secondary/50 border border-border/20 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
            />
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link to="/developers">
            <Button 
              className="bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 hover:border-primary/40 hover:shadow-[0_0_20px_rgba(20,255,236,0.15)] transition-all duration-300 gap-2 font-bold rounded-xl px-5 h-11"
            >
              <Code2 className="h-4 w-4" />
              <span className="hidden sm:inline">Developer Hub</span>
            </Button>
          </Link>
        </div>
      </div>
    </nav>
  );
};
