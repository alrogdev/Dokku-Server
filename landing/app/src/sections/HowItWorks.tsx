import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { 
  LogIn, 
  UserCog, 
  Link2, 
  History, 
  Rocket 
} from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

const steps = [
  {
    number: '01',
    icon: LogIn,
    title: 'Авторизация',
    description: 'OAuth через kimi.com — безопасный и быстрый вход без создания новых паролей.',
  },
  {
    number: '02',
    icon: UserCog,
    title: 'Выбор роли',
    description: 'Настройте агента под свои задачи за пару кликов.',
  },
  {
    number: '03',
    icon: Link2,
    title: 'Подключение интеграций',
    description: 'Подключение сервисов: read-only или с правами на изменение — вы контролируете.',
  },
  {
    number: '04',
    icon: History,
    title: 'Обучение',
    description: 'Обучение на исторических данных (опционально). Агент изучает ваши паттерны.',
  },
  {
    number: '05',
    icon: Rocket,
    title: 'Автономная работа',
    description: 'Автономная работа с подтверждением критических действий. Настраиваемый уровень контроля.',
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
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

export default function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const { isDark } = useTheme();

  return (
    <section 
      id="howitworks"
      className="relative py-20 lg:py-32 px-4 sm:px-6 lg:px-8"
      aria-label="Как это работает"
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
            <span className="gradient-text-purple-pink">Как это работает</span>
          </h2>
          <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Пять простых шагов от регистрации до полностью автономного AI-ассистента
          </p>
        </motion.div>

        {/* Steps */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="relative"
        >
          {/* Connection line (desktop) */}
          <div 
            className="hidden lg:block absolute top-16 left-[10%] right-[10%] h-px"
            style={{
              background: `linear-gradient(90deg, transparent, ${isDark ? 'rgba(139, 92, 246, 0.3)' : 'rgba(139, 92, 246, 0.2)'}, transparent)`,
            }}
          />
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-8">
            {steps.map((step, index) => (
              <motion.div
                key={step.number}
                variants={itemVariants}
                className="relative"
              >
                <div className="flex flex-col items-center text-center">
                  {/* Step number and icon */}
                  <div className="relative mb-4">
                    <div 
                      className="w-16 h-16 rounded-full flex items-center justify-center shadow-lg"
                      style={{
                        background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%)',
                        boxShadow: '0 4px 20px rgba(139, 92, 246, 0.3)',
                      }}
                    >
                      <step.icon className="w-7 h-7 text-white" aria-hidden="true" />
                    </div>
                    <span 
                      className="absolute -top-2 -right-2 w-6 h-6 rounded-full text-xs font-bold text-white flex items-center justify-center"
                      style={{
                        background: 'var(--accent-purple)',
                        border: `2px solid ${isDark ? '#0a0a0f' : '#ffffff'}`,
                      }}
                    >
                      {step.number}
                    </span>
                  </div>
                  
                  {/* Content */}
                  <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                    {step.title}
                  </h3>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                    {step.description}
                  </p>
                </div>
                
                {/* Arrow (mobile/tablet, except last) */}
                {index < steps.length - 1 && (
                  <div className="lg:hidden flex justify-center mt-6">
                    <div 
                      className="w-px h-8"
                      style={{
                        background: `linear-gradient(180deg, ${isDark ? 'rgba(139, 92, 246, 0.3)' : 'rgba(139, 92, 246, 0.2)'}, transparent)`,
                      }}
                    />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
