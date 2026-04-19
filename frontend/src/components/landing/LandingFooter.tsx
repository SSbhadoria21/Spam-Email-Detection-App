import { Github, Mail, Globe } from "lucide-react";
import { Link } from "react-router-dom";

export const LandingFooter = () => (
  <footer className="border-t border-border/40 py-16 bg-background">
    <div className="container mx-auto px-6 md:px-12">
      <div className="grid md:grid-cols-4 gap-12">
        <div className="col-span-2">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-1 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <img src="/favicon.ico" alt="App Logo" className="h-7 w-7" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              Spam Email <span className="text-primary">Detection</span>
            </span>
          </Link>
          <p className="text-muted-foreground max-w-sm leading-relaxed mb-6">
            Advanced algorithmic email security. Protect your inbox from phishing 
            and spam using statistical machine learning models.
          </p>
          <div className="flex gap-4">
            <a href="https://github.com/SSbhadoria21/Spam-Email-Detection-App" target="_blank" rel="noreferrer" className="p-2 rounded-full bg-muted/50 hover:bg-primary/10 hover:text-primary transition-all">
              <Github className="h-5 w-5" />
            </a>
            <a href="mailto:psemaildetection@gmail.com" className="p-2 rounded-full bg-muted/50 hover:bg-primary/10 hover:text-primary transition-all">
              <Mail className="h-5 w-5" />
            </a>
          </div>
        </div>
        
        <div>
          <h4 className="font-bold text-foreground mb-6 uppercase text-xs tracking-[0.2em]">Application</h4>
          <ul className="space-y-4 text-sm text-muted-foreground">
            <li><Link to="/#features" className="hover:text-primary transition-all">Features</Link></li>
            <li><Link to="/dashboard" className="hover:text-primary transition-all">Safety Dashboard</Link></li>
            <li><Link to="/dashboard/inbox" className="hover:text-primary transition-all">Gmail Scanner</Link></li>
            <li><Link to="/developers" className="hover:text-primary transition-all">Developers</Link></li>
          </ul>
        </div>

        <div>
          <h4 className="font-bold text-foreground mb-6 uppercase text-xs tracking-[0.2em]">Account</h4>
          <ul className="space-y-4 text-sm text-muted-foreground">
            <li><Link to="/login" className="hover:text-primary transition-colors">Sign In</Link></li>
            <li><Link to="/signup" className="hover:text-primary transition-colors">Create Account</Link></li>
          </ul>
        </div>
      </div>
      
      <div className="mt-16 pt-8 border-t border-border/40 flex flex-col md:flex-row justify-between items-center gap-4">
        <p className="text-xs text-muted-foreground">
          © {new Date().getFullYear()} Spam Email Detection App. Built for secure communication.
        </p>
        <div className="flex gap-8 text-xs text-muted-foreground/60">
          <Link to="/" className="hover:text-primary transition-colors">Privacy Policy</Link>
          <Link to="/" className="hover:text-primary transition-colors">Terms of Service</Link>
        </div>
      </div>
    </div>
  </footer>
);
