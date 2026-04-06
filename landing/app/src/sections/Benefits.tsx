import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { 
  Package, 
  Shield, 
  TrendingUp, 
  Plug, 
  Brain 
} from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

const benefits = [
  {
    icon: Package,
    title: 'Не собирай сам',
    description: 'Полностью managed инфраструктура, zero setup time. Мы настроили всё за вас — просто подключитесь и начните работать.',
    gradient: 'from-[var(--accent-purple)] to-[var(--accent-blue)]',
  },
  {
    icon: Shield,
    title: 'Безопасность данных',
    description: 'Enterprise-grade encryption, изоляция окружений, соответствие стандартам. Ваши данные под надёжной защитой.',
    gradient: 'from-[var(--accent-blue)] to-[var(--accent-cyan)]',
  },
  {
    icon: TrendingUp,
    title: 'Масштабируемость',
    description: 'От личного использования до enterprise deployment без изменения архитектуры. Растите без ограничений.',
    gradient: 'from-[var(--accent-cyan)] to-[var(--accent-purple)]',
  },
  {
    icon: Plug,
    title: 'Интеграции из коробки',
    description: '200+ готовых коннекторов: GitHub, Jira, Datadog, PagerDuty, публичные облака, VPS и многое другое.',
    gradient: 'from-[var(--accent-pink)] to-[var(--accent-purple)]',
  },
  {
    icon: Brain,
    title: 'Обучение на контексте',
    description: 'Агент адаптируется под ваши паттерны работы с течением времени. Чем дольше используете — тем умнее становится.',
    gradient: 'from-[var(--accent-blue)] to-[var(--accent-pink)]',
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
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: "easeOut" as const,
    },
  },
};

export default function Benefits() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const { isDark } = useTheme();

  return (
    <section 
      className="relative py-20 lg:py-32 px-4 sm:px-6 lg:px-8"
      aria-label="Преимущества подхода As a Service"
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
            <span style={{ color: 'var(--text-primary)' }}>Преимущества </span>
            <span className="gradient-text">подхода "As a Service"</span>
          </h2>
          <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Получите все преимущества автономных AI-агентов без сложностей развёртывания и поддержки инфраструктуры
          </p>
        </motion.div>

        {/* Benefits grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {benefits.map((benefit) => (
            <motion.div
              key={benefit.title}
              variants={itemVariants}
              className="group relative"
            >
              <div 
                className="relative h-full p-6 rounded-2xl transition-all duration-300 hover:scale-[1.02] hover:-translate-y-1"
                style={{
                  background: isDark ? 'rgba(26, 26, 36, 0.6)' : 'rgba(255, 255, 255, 0.7)',
                  backdropFilter: 'blur(12px)',
                  border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)'}`,
                }}
              >
                {/* Icon with gradient background */}
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${benefit.gradient} flex items-center justify-center mb-5 group-hover:shadow-lg transition-shadow duration-300`}>
                  <benefit.icon className="w-7 h-7 text-white" aria-hidden="true" />
                </div>
                
                {/* Content */}
                <h3 className="text-xl font-semibold mb-3" style={{ color: 'var(--text-primary)' }}>
                  {benefit.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {benefit.description}
                </p>
                
                {/* Hover glow effect */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${benefit.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300 -z-10 blur-xl`} />
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
