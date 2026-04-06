import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { Info } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

export default function Footer() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });
  const { isDark } = useTheme();

  return (
    <footer 
      className="relative py-12 lg:py-16 px-4 sm:px-6 lg:px-8"
      style={{ 
        backgroundColor: isDark ? '#0a0a0f' : '#f8f8fc',
        borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'}`,
      }}
      aria-label="Дисклеймер"
    >
      <div className="max-w-4xl mx-auto">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        >
          {/* Disclaimer header */}
          <div className="flex items-center gap-2 mb-4">
            <Info className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
            <h3 
              className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: 'var(--text-muted)' }}
            >
              Информационное уведомление
            </h3>
          </div>
          
          {/* Disclaimer text */}
          <div 
            className="space-y-3 text-xs sm:text-sm leading-relaxed"
            style={{ color: 'var(--text-muted)' }}
          >
            <p>
              <strong style={{ color: 'var(--text-primary)' }}>Kimi</strong> — зарегистрированная торговая марка Beijing Moonshot AI Technology Co., Ltd. 
              <strong style={{ color: 'var(--text-primary)' }}> Moonshot AI</strong> — торговая марка и наименование компании Beijing Moonshot AI Technology Co., Ltd.
            </p>
            <p>
              <strong style={{ color: 'var(--text-primary)' }}>Kimi K2.5</strong> — модель искусственного интеллекта компании Moonshot AI. 
              <strong style={{ color: 'var(--text-primary)' }}> Kimi CLI</strong> — интерфейс командной строки для работы с моделями Kimi.
            </p>
            <p>
              <strong style={{ color: 'var(--text-primary)' }}>Claude</strong> — зарегистрированная торговая марка Anthropic, PBC. 
              <strong style={{ color: 'var(--text-primary)' }}> Claude Code</strong> — продукт Anthropic, PBC.
            </p>
            <p>
              <strong style={{ color: 'var(--text-primary)' }}>Jira</strong> — зарегистрированная торговая марка Atlassian PTY LTD. 
              <strong style={{ color: 'var(--text-primary)' }}> GitHub</strong> — зарегистрированная торговая марка Microsoft Corporation. 
              <strong style={{ color: 'var(--text-primary)' }}> Datadog</strong> — зарегистрированная торговая марка Datadog, Inc.
            </p>
            <p>
              <strong style={{ color: 'var(--text-primary)' }}>KimiClaw</strong> — продукт <strong style={{ color: 'var(--text-primary)' }}>OpenClaw as a Service</strong> компании Moonshot. 
              Данная страница является информационной и не является официальным сайтом компании.
            </p>
            <p>
              Владелец сайта не получает финансового вознаграждения за размещение данной информации. 
              Эта страница создана как собственное мнение владельца относительно современных технологий 
              искусственного интеллекта.
            </p>
          </div>
          
          {/* Copyright */}
          <div 
            className="mt-8 pt-6 text-center"
            style={{ borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'}` }}
          >
            <p style={{ color: 'var(--text-muted)' }}>
              techclaw.ru © 2026
            </p>
          </div>
        </motion.div>
      </div>
    </footer>
  );
}
