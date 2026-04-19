import { motion } from "framer-motion";
import { ShieldCheck, Eye, Clock, Fingerprint, Globe, BarChart3 } from "lucide-react";

const benefits = [
  { icon: ShieldCheck, title: "99.7% Accuracy", desc: "Industry-leading spam detection powered by advanced classification engines" },
  { icon: Eye, title: "Phishing Protection", desc: "Identifies phishing attempts and malicious links instantly" },
  { icon: Clock, title: "Real-time Analysis", desc: "Get results in under 2 seconds for any email content" },
  { icon: Fingerprint, title: "Privacy First", desc: "Your emails are never stored — analyzed and discarded" },
  { icon: Globe, title: "Multi-language", desc: "Detects spam in 50+ languages with equal precision" },
  { icon: BarChart3, title: "Insightful Analytics", desc: "Detailed visualization of spam patterns and filtration metrics" },
];

export const BenefitsCarousel = () => {
  const doubled = [...benefits, ...benefits];

  return (
    <div className="py-24 overflow-hidden">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-16 px-6"
      >
        <h2 className="text-3xl md:text-5xl font-bold mb-4 text-foreground">
          Why Choose <span className="text-gradient-accent">Spam Detection</span>?
        </h2>
        <p className="text-muted-foreground max-w-xl mx-auto">
          Trusted by professionals worldwide to keep their inbox clean.
        </p>
      </motion.div>

      <div className="relative">
        <div className="flex gap-6 animate-slide-left" style={{ width: "max-content" }}>
          {doubled.map((b, i) => (
            <div
              key={i}
              className="w-80 flex-shrink-0 p-8 rounded-2xl bg-card border border-border hover:border-accent/40 transition-all"
            >
              <div className="inline-flex p-3 rounded-xl bg-accent/10 mb-5">
                <b.icon className="h-6 w-6 text-accent" />
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">{b.title}</h3>
              <p className="text-muted-foreground text-sm">{b.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
