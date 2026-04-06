import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { 
  Server, 
  Code2, 
  Webhook, 
  ClipboardList, 
  UserCheck 
} from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

const techDetails = [
  {
    icon: Server,
    title: 'Глобальная площадка',
    description: 'Надёжная инфраструктура с 99.9% uptime.',
  },
  {
    icon: Code2,
    title: 'API для интеграций',
    description: 'RESTful API для кастомных коннекторов.',
  },
  {
    icon: Webhook,
    title: 'Webhook support',
    description: 'Real-time events для мгновенной реакции.',
  },
  {
    icon: ClipboardList,
    title: 'Audit log',
    description: 'Полная история действий агента.',
  },
  {
    icon: UserCheck,
    title: 'Human-in-the-loop',
    description: 'Подтверждение критических операций.',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut" as const,
    },
  },
};

export default function TechDetails() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const { isDark } = useTheme();

  return (
    <section 
      className="relative py-20 lg:py-32 px-4 sm:px-6 lg:px-8"
      aria-label="Технические детали"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
            <span style={{ color: 'var(--text-primary)' }}>Технические </span>
            <span className="gradient-text">детали</span>
          </h2>
          <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Построено на современных технологиях для надёжности, безопасности и масштабируемости
          </p>
        </motion.div>

        {/* Tech details grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {techDetails.map((detail) => (
            <motion.div
              key={detail.title}
              variants={itemVariants}
              className="group"
            >
              <div 
                className="flex items-start gap-4 p-5 rounded-xl transition-all duration-300"
                style={{
                  background: isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
                  border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)'}`,
                }}
              >
                {/* Icon */}
                <div 
                  className="flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center transition-colors duration-300"
                  style={{ background: 'rgba(139, 92, 246, 0.1)' }}
                >
                  <detail.icon className="w-5 h-5" style={{ color: 'var(--accent-purple)' }} />
                </div>
                
                {/* Content */}
                <div>
                  <h3 className="text-base font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                    {detail.title}
                  </h3>
                  <p className="text-xs leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                    {detail.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
