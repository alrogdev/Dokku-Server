import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { 
  FileText, 
  Image, 
  Languages, 
  Code2, 
  Cloud,
  Shield
} from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

const features = [
  {
    icon: FileText,
    title: 'Длинный контекст',
    description: '256K токенов для глубокого анализа документов и сложных задач. Обрабатывайте целые книги и длинные кодовые базы за один запрос.',
    gradient: 'from-[var(--accent-purple)] to-[var(--accent-blue)]',
  },
  {
    icon: Image,
    title: 'Мультимодальность',
    description: 'Текст, код, изображения — всё в одной модели. Анализируйте скриншоты, диаграммы и фото вместе с текстовым контекстом.',
    gradient: 'from-[var(--accent-blue)] to-[var(--accent-cyan)]',
  },
  {
    icon: Languages,
    title: 'Русский язык',
    description: 'Отличное понимание русского языка и культурного контекста. Нюансы, идиомы и специфика — всё учитывается в ответах.',
    gradient: 'from-[var(--accent-cyan)] to-[var(--accent-purple)]',
  },
  {
    icon: Code2,
    title: 'Программирование',
    description: 'Высокая компетентность в коде и системном администрировании. От скриптов до архитектуры распределённых систем.',
    gradient: 'from-[var(--accent-pink)] to-[var(--accent-purple)]',
  },
  {
    icon: Cloud,
    title: 'Облачная доступность',
    description: 'Без настройки собственной инфраструктуры. Подключайтесь и начинайте работать за минуты, а не дни.',
    gradient: 'from-[var(--accent-blue)] to-[var(--accent-pink)]',
  },
  {
    icon: Shield,
    title: 'Открытая модель',
    description: 'Kimi K2.5 — открытая модель, которую можно развернуть в собственном контуре. Полный контроль над данными и инфраструктурой.',
    gradient: 'from-[var(--accent-purple)] to-[var(--accent-cyan)]',
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

export default function Features() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const { isDark } = useTheme();

  return (
    <section 
      id="features"
      className="relative py-20 lg:py-32 px-4 sm:px-6 lg:px-8"
      aria-label="Преимущества модели Kimi K2.5"
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
            <span className="gradient-text">Модель Kimi K2.5</span>
          </h2>
          <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Самая передовая модель для автономных агентов. Сочетает мощь большого контекста с мультимодальными возможностями.
          </p>
        </motion.div>

        {/* Features grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.title}
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
                {/* Icon */}
                <div 
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4 group-hover:shadow-lg transition-shadow duration-300`}
                >
                  <feature.icon className="w-6 h-6 text-white" aria-hidden="true" />
                </div>
                
                {/* Content */}
                <h3 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
                  {feature.title}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>
                  {feature.description}
                </p>
                
                {/* Hover glow */}
                <div 
                  className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300 -z-10 blur-xl`} 
                />
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
