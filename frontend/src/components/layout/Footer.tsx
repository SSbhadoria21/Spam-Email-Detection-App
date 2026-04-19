import { Shield } from "lucide-react";

export const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full px-6 py-12 mt-auto border-t border-border/20 bg-background/20 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start gap-8 mb-10">
          <div className="flex items-center gap-5">
            <div className="h-16 w-16 rounded-2xl bg-white flex items-center justify-center shadow-lg border border-border/50 p-2 overflow-hidden">
              <img src="/favicon.ico" alt="Logo" className="h-full w-full object-contain" />
            </div>
            <div className="space-y-1">
              <h3 className="text-xl font-black tracking-tight text-foreground uppercase italic">
                Spam Email Detection App
              </h3>
              <p className="text-sm font-bold text-muted-foreground uppercase tracking-widest">
                Academic Project | MITS-DU, Gwalior
              </p>
            </div>
          </div>

          <div className="max-w-md text-right md:ml-auto">
            <p className="text-xs font-bold text-muted-foreground leading-relaxed uppercase tracking-wider">
              High-performance algorithmic filtration <br /> 
              Protecting digital identities from evolving spam threats.
            </p>
          </div>
        </div>

        <div className="pt-8 border-t border-border/10 flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="text-[11px] font-black text-muted-foreground uppercase tracking-[0.2em]">
            © {currentYear} SPAM EMAIL DETECTION, MITS GWALIOR
          </div>
          <div className="text-[11px] font-black text-muted-foreground uppercase tracking-[0.2em] flex items-center gap-2">
            Developed by <span className="text-primary italic">Prateek A. Batham & Sumit S. Bhadoria</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
