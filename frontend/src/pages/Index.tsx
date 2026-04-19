import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Shield, Zap, Lock, Mail, ArrowRight, ChevronDown, User, LogOut, Settings, Inbox, LayoutDashboard, Github, Cpu, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext";
import { LandingFooter } from "@/components/landing/LandingFooter";
import { ThreeDCard } from "@/components/landing/ThreeDCard";

const Index = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden font-sans">
      {/* Navbar */}
      <motion.nav
        initial={{ y: -80 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 backdrop-blur-xl bg-background/60"
      >
        <div className="container mx-auto flex items-center justify-between py-4 px-6 md:px-12">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="p-1 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
              <img src="/favicon.ico" alt="Dashboard Logo" className="h-8 w-8 drop-shadow-[0_0_8px_rgba(20,255,236,0.3)]" />
            </div>
            <span className="text-xl font-bold tracking-tight">
              Spam Email <span className="text-primary">Detection</span>
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground font-medium">
            <a href="/#features" className="hover:text-primary transition-all hover:tracking-wider">Features</a>
            <Link to="/developers" className="hover:text-primary transition-all hover:tracking-wider">Developers</Link>
            <a href="https://github.com/SSbhadoria21/Spam-Email-Detection-App" target="_blank" className="hover:text-primary transition-all hover:tracking-wider">Github</a>
          </div>
          
          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-3">
                <Link to="/dashboard" className="hidden sm:block">
                  <Button variant="ghost" className="text-muted-foreground hover:text-primary gap-2 transition-all">
                    <LayoutDashboard className="h-4 w-4" />
                    Dashboard
                  </Button>
                </Link>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" className="relative h-10 w-10 rounded-full border border-border p-0 overflow-hidden hover:border-primary/50 transition-colors">
                      <Avatar className="h-full w-full">
                        {user.picture ? (
                          <AvatarImage src={user.picture} alt={user.name} referrerPolicy="no-referrer" />
                        ) : (
                          <AvatarFallback className="bg-primary/10 text-primary uppercase text-xs">
                            {user.name ? user.name.charAt(0) : "U"}
                          </AvatarFallback>
                        )}
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent className="w-56 mt-2" align="end" forceMount>
                    <DropdownMenuLabel className="font-normal border-b pb-2 mb-2 border-border/50">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none">{user.name}</p>
                        <p className="text-xs leading-none text-muted-foreground truncate">
                          {user.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <Link to="/dashboard/profile">
                      <DropdownMenuItem className="cursor-pointer gap-2 focus:bg-primary/10 py-2.5">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span>Profile</span>
                      </DropdownMenuItem>
                    </Link>
                    <DropdownMenuItem
                      className="cursor-pointer text-destructive focus:bg-destructive/10 focus:text-destructive gap-2 py-2.5"
                      onClick={logout}
                    >
                      <LogOut className="h-4 w-4" />
                      <span>Log out</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/login">
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button variant="ghost" className="text-muted-foreground hover:text-primary font-medium">
                      Login
                    </Button>
                  </motion.div>
                </Link>
                <Link to="/signup">
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button className="bg-primary text-primary-foreground hover:opacity-90 shadow-[0_0_20px_rgba(20,255,236,0.3)] px-6 font-bold rounded-xl relative overflow-hidden group">
                      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-[shimmer_1.5s_infinite] pointer-events-none" />
                      Get Started
                    </Button>
                  </motion.div>
                </Link>
              </div>
            )}
          </div>
        </div>
      </motion.nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-24 px-6 overflow-hidden bg-[radial-gradient(circle_at_50%_50%,rgba(17,24,39,1)_0%,rgba(3,7,18,1)_100%)]">
        <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 -left-1/4 w-[50%] h-[50%] bg-primary/5 rounded-full blur-[120px]" />
          <div className="absolute bottom-1/4 -right-1/4 w-[40%] h-[40%] bg-accent/5 rounded-full blur-[120px]" />
        </div>

        <div className="container mx-auto relative z-10 grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="text-left"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/20 bg-primary/5 mb-6">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
              </span>
              <span className="text-xs font-semibold text-primary uppercase tracking-wider">Powered by Machine Learning</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold leading-[1.1] mb-8 tracking-tight">
              Next-Gen <br /> 
              <span className="text-primary italic">Algorithmic Security</span> <br />
              for your Inbox.
            </h1>
            
            <p className="text-lg md:text-xl text-muted-foreground max-w-xl mb-10 leading-relaxed">
              Experience zero-trust email analysis. Our Naive Bayes model detects 
              phishing and spam patterns in real-time with unparalleled precision.
            </p>

            <div className="flex flex-col sm:flex-row items-center gap-5">
              <Link to={user ? "/dashboard" : "/signup"}>
                <motion.div whileHover={{ y: -4 }} transition={{ type: "spring", stiffness: 400, damping: 10 }}>
                  <Button size="lg" className="h-14 px-8 bg-primary text-primary-foreground hover:opacity-90 text-md font-bold rounded-xl gap-2 shadow-[0_4px_25px_rgba(20,255,236,0.4)] relative overflow-hidden group">
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_2s_infinite] pointer-events-none" />
                    {user ? "Open Dashboard" : "Start Protecting Now"}
                    <ArrowRight className="h-5 w-5 group-hover:translate-x-2 transition-all" />
                  </Button>
                </motion.div>
              </Link>
              <a href="https://github.com/SSbhadoria21/Spam-Email-Detection-App" target="_blank" rel="noreferrer">
                <motion.div whileHover={{ y: -4 }} transition={{ type: "spring", stiffness: 400, damping: 10 }}>
                  <Button size="lg" variant="outline" className="h-14 px-8 border-border hover:bg-muted/50 text-md rounded-xl gap-2 font-medium">
                    <Github className="h-5 w-5" />
                    View Source
                  </Button>
                </motion.div>
              </a>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8, rotateY: 20 }}
            animate={{ opacity: 1, scale: 1, rotateY: 0 }}
            transition={{ duration: 1, delay: 0.2 }}
            className="hidden lg:block perspective-1000"
          >
            <ThreeDCard className="max-w-md mx-auto">
              <div className="relative p-1 rounded-3xl bg-gradient-to-br from-primary/20 to-accent/20 backdrop-blur-3xl overflow-hidden border border-white/5">
                <div className="bg-background/90 rounded-[calc(1.5rem-2px)] p-8 h-[500px] flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-12">
                      <div className="h-12 w-12 rounded-2xl bg-primary/20 flex items-center justify-center border border-primary/30">
                        <Cpu className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex gap-1">
                        {[1, 2, 3].map(i => <div key={i} className="h-1.5 w-1.5 rounded-full bg-primary/40" />)}
                      </div>
                    </div>
                    
                    <h3 className="text-2xl font-bold text-foreground mb-4">Algorithmic Scanner v1.0</h3>
                    <div className="space-y-4">
                      <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                        <motion.div 
                          className="h-full bg-primary"
                          initial={{ width: 0 }}
                          animate={{ width: "97%" }}
                          transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
                        />
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        Scanning incoming payload... Identifying statistical weight of keywords. 
                        Cross-referencing Naive Bayes dataset for probability distribution.
                      </p>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-white/5 border border-white/5 mt-auto">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-muted-foreground italic">Current Safety Level</span>
                      <span className="text-xs font-bold text-primary">Ultra Secure</span>
                    </div>
                    <div className="text-2xl font-bold font-mono text-foreground tracking-tighter">
                      99.78% <span className="text-sm font-normal text-muted-foreground">confidence</span>
                    </div>
                  </div>
                </div>
              </div>
            </ThreeDCard>
          </motion.div>
        </div>

        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-10 left-1/2 -translate-x-1/2 cursor-pointer z-10"
          onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}
        >
          <div className="flex flex-col items-center gap-2">
            <span className="text-[10px] uppercase font-bold tracking-[0.2em] text-muted-foreground/60">The Tech</span>
            <ChevronDown className="h-5 w-5 text-muted-foreground/40" />
          </div>
        </motion.div>
      </section>

      {/* Modern Features Grid */}
      <section id="features" className="py-32 relative z-10 container mx-auto px-6">
        <div className="text-center mb-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-block px-4 py-1 rounded-full bg-primary/10 border border-primary/20 text-xs font-bold text-primary mb-6 uppercase tracking-widest"
          >
            Core Infrastructure
          </motion.div>
          <h2 className="text-4xl md:text-5xl font-bold mb-6">Minimalistic. Power-packed.</h2>
          <p className="text-muted-foreground max-w-xl mx-auto text-lg leading-relaxed">
            We stripped away the noise. Only the tools you need to stay secure in the modern digital age.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            { 
              icon: Zap, 
              title: "Naive Bayes Engine", 
              desc: "Fast, lightweight, and effective. Our model calculates spam probability using high-dimensional feature vectors.",
              color: "text-primary",
              bg: "bg-primary/10"
            },
            { 
              icon: Inbox, 
              title: "Gmail Connect v2", 
              desc: "Direct integration with Gmail API for seamless inbox scanning without compromising account security.",
              color: "text-accent",
              bg: "bg-accent/10"
            },
            { 
              icon: Database, 
              title: "Firestore History", 
              desc: "Permanent, secure storage of scan history with real-time sync across all your devices.",
              color: "text-primary",
              bg: "bg-primary/10"
            },
          ].map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -10 }}
              className="p-10 rounded-3xl bg-card border border-border/60 hover:border-primary/50 transition-all duration-300 relative group overflow-hidden"
            >
              <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                <feature.icon className={`h-24 w-24 ${feature.color}`} />
              </div>
              
              <div className={`h-12 w-12 rounded-xl ${feature.bg} flex items-center justify-center mb-8`}>
                <feature.icon className={`h-6 w-6 ${feature.color}`} />
              </div>
              
              <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
              <p className="text-muted-foreground leading-relaxed">
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6">
        <div className="container mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="p-12 md:p-20 rounded-[3rem] bg-gradient-to-br from-primary/10 via-background to-accent/10 border border-border/50 text-center relative overflow-hidden"
          >
            <div className="absolute -top-24 -left-24 w-64 h-64 bg-primary/10 rounded-full blur-[80px]" />
            <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-accent/10 rounded-full blur-[80px]" />
            
            <div className="relative z-10">
              <h2 className="text-4xl md:text-5xl font-bold mb-6">Security Simplified.</h2>
              <p className="text-muted-foreground text-lg mb-10 max-w-lg mx-auto leading-relaxed">
                No credit cards. No false promises. Just actual advanced protection for your digital communication.
              </p>
              <Link to={user ? "/dashboard" : "/signup"}>
                <Button size="lg" className="h-16 px-12 bg-primary text-primary-foreground text-lg font-bold rounded-2xl shadow-xl hover:scale-105 transition-transform">
                  {user ? "Back to Dashboard" : "Create Your Secure Inbox"}
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <LandingFooter />
    </div>
  );
};

export default Index;
