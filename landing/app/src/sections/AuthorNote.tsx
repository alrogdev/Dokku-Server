import { motion, useInView } from 'framer-motion';
import { useRef } from 'react';
import { Quote, ExternalLink } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';

export default function AuthorNote() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });
  const { isDark } = useTheme();

  return (
    <section 
      id="about"
      className="relative py-20 lg:py-32 px-4 sm:px-6 lg:px-8"
      aria-label="Мнение автора"
    >
      <div className="max-w-4xl mx-auto">
        <motion.div
          ref={ref}
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, ease: [0.25, 0.1, 0.25, 1] }}
          className="relative"
        >
          {/* Author note card with warm background */}
          <div 
            className="relative rounded-3xl p-8 lg:p-12 shadow-2xl"
            style={{ 
              backgroundColor: isDark ? '#1a1814' : '#faf8f5',
              border: `1px solid ${isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'}`,
            }}
          >
            {/* Quote icon */}
            <div 
              className="absolute -top-6 left-8 w-12 h-12 rounded-full flex items-center justify-center shadow-lg"
              style={{
                background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%)',
              }}
            >
              <Quote className="w-6 h-6 text-white" aria-hidden="true" />
            </div>
            
            {/* Header */}
            <div className="mb-8 pt-4">
              <h2 
                className="text-2xl sm:text-3xl font-bold mb-2"
                style={{ color: isDark ? '#f5f0e8' : '#1a1814' }}
              >
                Момент осознания
              </h2>
              <p style={{ color: isDark ? '#a8a29e' : '#78716c' }}>
                Личные размышения автора о трансформации, которую приносят автономные AI-агенты
              </p>
            </div>
            
            {/* Content */}
            <div 
              className="space-y-4 text-sm leading-relaxed"
              style={{ color: isDark ? '#d6d3d1' : '#44403c' }}
            >
              <p>
                В феврале 2026 года я наткнулся на эссе Мэтта Шумера 
                <a 
                  href="https://shumer.dev/something-big-is-happening" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mx-1 transition-colors underline underline-offset-2"
                  style={{ color: 'var(--accent-purple)' }}
                >
                  "Something Big Is Happening"
                  <ExternalLink className="w-3 h-3" />
                </a>
                <a 
                  href="https://pikabu.ru/story/ai_zamenit_vsekh_ili_svodka_po_state_something_big_is_happening_by_matt_shumer_13751785" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 ml-1 transition-colors underline underline-offset-2"
                  style={{ color: 'var(--accent-purple)' }}
                >
                  (перевод
                  <ExternalLink className="w-3 h-3" />)
                </a>. 
                Не могу сказать, что это был шок — скорее, тихое, но ощутимое смещение фундамента.
              </p>
              
              <p>
                До этого момента я уже считал себя вполне "в теме": использую Perplexity с 2022 года для исследований, 
                не работаю с Deep Research без проверки источников, среди коллег и друзей меня знают как человека, 
                который "давно разобрался с ИИ". Я привык воспринимать эти инструменты как эффективные, но всё же — инструменты. 
                Улучшенные отвёртки для интеллектуального труда.
              </p>
              
              <p 
                className="font-medium"
                style={{ color: isDark ? '#f5f0e8' : '#1a1814' }}
              >
                Но Шумер описал нечто другое. Не улучшение, а смена формата.
              </p>
              
              <p>
                Когда я начал разбираться — действительно ли что-то изменилось с февраля 2026 года — я понял, 
                что изменился не просто набор функций. Мы наблюдаем рождение новой категории сущностей: 
                OpenCode, Claude Code, Kimi CLI, автономные DevOps-агенты, системы AppSec-автоматизации, OpenClaw. 
                Это уже не "помощники", требующие постоянного контроля и подсказок на каждом шагу. 
                Это агенты, способные держать контекст, принимать решения и действовать самостоятельно — 
                порой более компетентно, чем мы сами.
              </p>
              
              <p 
                className="font-medium"
                style={{ color: isDark ? '#f5f0e8' : '#1a1814' }}
              >
                Я пришёл к выводу, который нельзя игнорировать: это не очередная технологическая волна, 
                которую можно оседлать или не замечать. Это изменение ландшафта самой деятельности. 
                Мы не выбираем, адаптироваться или нет — мы выбираем только, осознаём ли мы происходящее 
                и готовы ли учиться заново.
              </p>
              
              <p>
                Эта страница — не манифест и не инструкция. Это просто моя личная попытка удержать мысль 
                о том, как быстро обычное становится устаревшим. И приглашение задуматься вместе со мной: 
                что из того, что мы считаем своей профессиональной неприкосновенностью, уже начало трансформироваться 
                без нашего участия?
              </p>
            </div>
            
            {/* Signature */}
            <div 
              className="mt-8 pt-6 border-t"
              style={{ borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' }}
            >
              <p style={{ color: isDark ? '#a8a29e' : '#78716c' }} className="italic">
                — Автор страницы, апрель 2026
              </p>
            </div>
          </div>
          
          {/* Decorative elements */}
          <div 
            className="absolute -bottom-4 -right-4 w-24 h-24 rounded-full blur-2xl"
            style={{ background: 'rgba(139, 92, 246, 0.1)' }}
          />
          <div 
            className="absolute -top-4 -left-4 w-20 h-20 rounded-full blur-2xl"
            style={{ background: 'rgba(59, 130, 246, 0.1)' }}
          />
        </motion.div>
      </div>
    </section>
  );
}
