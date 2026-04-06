import { useEffect } from 'react';
import Navigation from './sections/Navigation';
import Hero from './sections/Hero';
import Features from './sections/Features';
import UseCases from './sections/UseCases';
import Benefits from './sections/Benefits';
import HowItWorks from './sections/HowItWorks';
import TechDetails from './sections/TechDetails';
import AuthorNote from './sections/AuthorNote';
import Footer from './sections/Footer';
import { useTheme } from './hooks/useTheme';

function AppContent() {
  const { theme } = useTheme();

  useEffect(() => {
    // Apply theme class to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <div 
      className="min-h-screen overflow-x-hidden transition-colors duration-300"
      style={{ 
        backgroundColor: 'var(--bg-primary)',
        color: 'var(--text-primary)',
      }}
    >
      {/* Background gradient effects */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div 
          className="absolute top-0 left-1/4 w-[600px] h-[600px] rounded-full blur-[150px] animate-pulse-slow"
          style={{ background: 'rgba(139, 92, 246, 0.08)' }}
        />
        <div 
          className="absolute top-1/3 right-1/4 w-[500px] h-[500px] rounded-full blur-[120px] animate-pulse-slow"
          style={{ 
            background: 'rgba(59, 130, 246, 0.06)',
            animationDelay: '2s' 
          }}
        />
        <div 
          className="absolute bottom-1/4 left-1/3 w-[400px] h-[400px] rounded-full blur-[100px] animate-pulse-slow"
          style={{ 
            background: 'rgba(6, 182, 212, 0.04)',
            animationDelay: '4s' 
          }}
        />
      </div>

      {/* Navigation */}
      <Navigation />

      {/* Main content */}
      <main className="relative z-10">
        <Hero />
        <Features />
        <UseCases />
        <Benefits />
        <HowItWorks />
        <TechDetails />
        <AuthorNote />
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}

function App() {
  return <AppContent />;
}

export default App;
