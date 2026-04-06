import { motion, AnimatePresence, useInView } from 'framer-motion';
import { useRef, useState } from 'react';
import { 
  User, Terminal, Shield, BarChart3, Lock,
  Check
} from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

const roles = [
  {
    id: 'personal',
    label: 'Личный помощник',
    icon: User,
    tasks: [
      'Автоматическое управление календарём: анализ приглашений, перенос встреч при конфликтах без вашего участия, поиск свободных слотов',
      'Интеллектуальная фильтрация почты: приоритизация срочных писем, мьютинг неважной корреспонденции во время фокус-работы (deep work)',
      'Интеграция с мессенджерами: общение в привычной среде, управление задачами через естественный язык',
      'Контекстное напоминание: "У тебя через 15 мин встреча, но ты ещё не выехал — пробки на маршруте"',
    ],
  },
  {
    id: 'devops',
    label: 'DevOps инженер',
    icon: Terminal,
    tasks: [
      'Автоматизация CI/CD: анализ ошибок сборок в реальном времени, автоматические pull requests с фиксами, оптимизация pipeline',
      'Инфраструктура как код: генерация конфигураций Terraform/Ansible, аудит безопасности, проверка best practices',
      'Управление секретами: мониторинг expiration сертификатов и токенов, автоматическая ротация, интеграция с менеджерами секретов',
      'Cost optimization: анализ использования ресурсов публичного облака и VPS, рекомендации по downsizing, удаление неиспользуемых ресурсов',
      'Мониторинг и алерты: агрегация логов из multiple sources, умная группировка алертов (deduplication), предиктивное масштабирование',
    ],
  },
  {
    id: 'sre',
    label: 'SRE инженер',
    icon: Shield,
    tasks: [
      'Incident management: автоматический root cause analysis, генерация постмортемов, эскалация по playbook',
      'SLO/SLA tracking: автоматический расчёт error budget, прогнозирование нарушений SLA, рекомендации по корректировке целей',
      'Chaos engineering: планирование тестов отказоустойчивости, анализ результатов, предложение улучшений архитектуры',
      'Release management: канареечные деплои с автоматическим мониторингом метрик, auto-rollback при деградации latency/error rate',
      'Runbook automation: авто-генерация документации из решённых инцидентов, обновление процедур по мере изменения системы',
    ],
  },
  {
    id: 'pm',
    label: 'Product Manager',
    icon: BarChart3,
    tasks: [
      'Анализ пользовательской аналитики: автоматическая генерация отчётов по метрикам продукта, выявление трендов',
      'Управление бэклогом: приоритизация фич на основе данных, оценка technical debt, написание PRD и user stories',
      'Competitive analysis: мониторинг конкурентов, алертинг о новых фичах, рекомендации по позиционированию',
    ],
  },
  {
    id: 'security',
    label: 'Security Analyst',
    icon: Lock,
    tasks: [
      'Threat monitoring: анализ security logs, выявление аномалий, корреляция инцидентов',
      'Vulnerability management: сканирование dependencies, автоматические PR с обновлениями security patches',
      'Compliance monitoring: проверка соответствия SOC2/GDPR/ISO, автоматический сбор доказательств для аудитов',
    ],
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: 0.3,
      ease: "easeOut" as const,
    },
  },
};

export default function UseCases() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const [activeRole, setActiveRole] = useState('personal');
  const { isDark } = useTheme();

  const activeRoleData = roles.find(r => r.id === activeRole);

  return (
    <section 
      id="usecases"
      className="relative py-20 lg:py-32 px-4 sm:px-6 lg:px-8"
      aria-label="Кейсы использования"
    >
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4" style={{ color: 'var(--text-primary)' }}>
            <span style={{ color: 'var(--text-primary)' }}>Кейсы </span>
            <span className="gradient-text-purple-pink">использования</span>
          </h2>
          <p className="text-lg max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            KimiClaw адаптируется под вашу роль и берёт на себя рутинные задачи, позволяя сфокусироваться на стратегии
          </p>
        </motion.div>

        {/* Role tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1], delay: 0.1 }}
          className="flex flex-wrap justify-center gap-2 mb-10"
          role="tablist"
          aria-label="Выбор роли"
        >
          {roles.map((role) => (
            <button
              key={role.id}
              onClick={() => setActiveRole(role.id)}
              role="tab"
              aria-selected={activeRole === role.id}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                activeRole === role.id
                  ? 'text-white shadow-lg'
                  : 'transition-colors'
              }`}
              style={{
                background: activeRole === role.id
                  ? 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%)'
                  : isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.05)',
                color: activeRole === role.id ? 'white' : 'var(--text-secondary)',
                boxShadow: activeRole === role.id ? '0 4px 20px rgba(139, 92, 246, 0.3)' : 'none',
              }}
            >
              <role.icon className="w-4 h-4" aria-hidden="true" />
              {role.label}
            </button>
          ))}
        </motion.div>

        {/* Content panel */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeRole}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="rounded-2xl p-6 lg:p-8"
            style={{
              background: isDark ? 'rgba(26, 26, 36, 0.6)' : 'rgba(255, 255, 255, 0.7)',
              backdropFilter: 'blur(12px)',
              border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)'}`,
            }}
          >
            <div className="flex items-center gap-3 mb-6">
              <div 
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%)',
                }}
              >
                {activeRoleData && <activeRoleData.icon className="w-5 h-5 text-white" aria-hidden="true" />}
              </div>
              <h3 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>
                {activeRoleData?.label}
              </h3>
            </div>

            <motion.ul
              variants={containerVariants}
              initial="hidden"
              animate="visible"
              className="space-y-4"
            >
              {activeRoleData?.tasks.map((task, index) => (
                <motion.li
                  key={index}
                  variants={itemVariants}
                  className="flex items-start gap-3"
                >
                  <div 
                    className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5"
                    style={{ background: 'rgba(139, 92, 246, 0.2)' }}
                  >
                    <Check className="w-3.5 h-3.5" style={{ color: 'var(--accent-purple)' }} />
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{task}</span>
                  </div>
                </motion.li>
              ))}
            </motion.ul>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
