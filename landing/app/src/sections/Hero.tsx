import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.15,
    },
  },
};

export default function Hero() {
  const { isDark } = useTheme();

  return (
    <section 
      className="relative min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 py-20 pt-24"
      aria-label="Hero section"
    >
      {/* Background gradient effects */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div 
          className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full blur-[150px] animate-pulse-slow"
          style={{ background: isDark ? 'rgba(139, 92, 246, 0.2)' : 'rgba(139, 92, 246, 0.15)' }}
        />
        <div 
          className="absolute top-1/3 right-1/4 w-[500px] h-[500px] rounded-full blur-[120px] animate-pulse-slow"
          style={{ 
            background: isDark ? 'rgba(59, 130, 246, 0.15)' : 'rgba(59, 130, 246, 0.1)',
            animationDelay: '2s' 
          }}
        />
        <div 
          className="absolute bottom-1/4 left-1/3 w-[400px] h-[400px] rounded-full blur-[100px] animate-pulse-slow"
          style={{ 
            background: isDark ? 'rgba(6, 182, 212, 0.1)' : 'rgba(6, 182, 212, 0.08)',
            animationDelay: '4s' 
          }}
        />
      </div>
      
      {/* Grid pattern overlay */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} 1px, transparent 1px),
                           linear-gradient(90deg, ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'} 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />
      
      <motion.div 
        className="max-w-6xl mx-auto w-full relative z-10"
        variants={staggerContainer}
        initial="initial"
        animate="animate"
      >
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Text content */}
          <div className="text-center lg:text-left order-2 lg:order-1">
            <motion.div
              variants={fadeInUp}
              transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
            >
              <span 
                className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium mb-6"
                style={{
                  background: isDark ? 'rgba(26, 26, 36, 0.6)' : 'rgba(255, 255, 255, 0.7)',
                  backdropFilter: 'blur(12px)',
                  border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)'}`,
                  color: 'var(--accent-purple)',
                }}
              >
                <Sparkles className="w-4 h-4" aria-hidden="true" />
                OpenClaw as a Service
              </span>
            </motion.div>
            
            <motion.h1
              variants={fadeInUp}
              transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1], delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6"
              style={{ color: 'var(--text-primary)' }}
            >
              <span className="gradient-text">KimiClaw</span>
              <span style={{ color: 'var(--text-primary)' }}> — Ваш автономный AI-ассистент в облаке</span>
            </motion.h1>
            
            <motion.p
              variants={fadeInUp}
              transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1], delay: 0.2 }}
              className="text-lg sm:text-xl mb-8 max-w-xl mx-auto lg:mx-0"
              style={{ color: 'var(--text-secondary)' }}
            >
              OpenClaw as a Service на базе Kimi K2.5. Подключите почту, календарь, мессенджеры и получите компетентного помощника, который действует самостоятельно
            </motion.p>
            
            <motion.div
              variants={fadeInUp}
              transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1], delay: 0.3 }}
              className="flex justify-center lg:justify-start"
            >
              <a 
                href="#about" 
                className="group relative overflow-hidden text-white font-semibold px-8 py-4 text-lg rounded-xl transition-all duration-300 hover:scale-[1.02] inline-flex items-center justify-center gap-2"
                style={{
                  background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 50%, var(--accent-cyan) 100%)',
                  boxShadow: isDark 
                    ? '0 0 40px rgba(139, 92, 246, 0.3)' 
                    : '0 4px 20px rgba(139, 92, 246, 0.25)',
                }}
              >
                Момент осознания
              </a>
            </motion.div>
          </div>
          
          {/* Illustration */}
          <motion.div
            variants={fadeInUp}
            transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1], delay: 0.2 }}
            className="relative order-1 lg:order-2 flex justify-center"
          >
            <motion.div
              animate={{ y: [0, -20, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              className="relative"
            >
              <img
                src="/hero-illustration.png"
                alt="Облачная инфраструктура с AI-агентом"
                className="w-full max-w-lg lg:max-w-xl h-auto drop-shadow-2xl"
                loading="eager"
              />
            </motion.div>
          </motion.div>
        </div>
      </motion.div>
      
      {/* Scroll indicator */}
      <motion.div 
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1, duration: 0.5 }}
      >
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          className="w-6 h-10 rounded-full flex justify-center pt-2"
          style={{
            border: `2px solid ${isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)'}`,
          }}
        >
          <div 
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: isDark ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)' }}
          />
        </motion.div>
      </motion.div>
    </section>
  );
}
