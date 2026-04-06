# KimiClaw — Техническая спецификация

## 1. Технологический стек

- **Framework**: React 18 + TypeScript
- **Build**: Vite 7.2.4
- **Styling**: Tailwind CSS 3.4.19
- **UI Components**: shadcn/ui (40+ pre-installed components)
- **Icons**: Lucide React
- **Animations**: Framer Motion
- **Fonts**: Inter (Google Fonts)

## 2. Структура проекта

```
src/
├── sections/
│   ├── Hero.tsx              # Hero секция с CTA
│   ├── Features.tsx          # Преимущества Kimi K2.5
│   ├── UseCases.tsx          # Кейсы использования (табы)
│   ├── Benefits.tsx          # Преимущества As a Service
│   ├── HowItWorks.tsx        # Как это работает (timeline)
│   ├── TechDetails.tsx       # Технические детали
│   ├── AuthorNote.tsx        # Мнение автора
│   └── Footer.tsx            # Дисклеймер
├── components/
│   ├── ui/                   # shadcn/ui components
│   ├── GradientText.tsx      # Градиентный текст
│   ├── GlassCard.tsx         # Glassmorphism карточка
│   ├── GradientButton.tsx    # Кнопка с градиентом
│   └── AnimatedSection.tsx   # Обёртка для scroll-анимаций
├── hooks/
│   └── useScrollAnimation.ts # Hook для intersection observer
├── lib/
│   └── utils.ts              # Утилиты (cn функция)
├── App.tsx                   # Главный компонент
├── index.css                 # Глобальные стили
└── main.tsx                  # Entry point
```

## 3. Компоненты

### UI Components (shadcn/ui)

- Button — CTA кнопки
- Card — карточки преимуществ
- Tabs — переключение ролей в Use Cases
- Badge — метки и теги
- Accordion — мобильная версия Use Cases (опционально)
- Separator — разделители

### Custom Components

**GradientText**
```tsx
interface GradientTextProps {
  children: React.ReactNode;
  className?: string;
  from?: string;
  to?: string;
}
```

**GlassCard**
```tsx
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}
```

**GradientButton**
```tsx
interface GradientButtonProps {
  children: React.ReactNode;
  href: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}
```

**AnimatedSection**
```tsx
interface AnimatedSectionProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}
```

## 4. Анимации

### Framer Motion конфигурация

```tsx
// Fade in from bottom
const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }
};

// Stagger children
const stagger = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

// Scale on hover
const hoverScale = {
  whileHover: { scale: 1.02 },
  whileTap: { scale: 0.98 }
};
```

### CSS анимации

```css
/* Float animation for hero illustration */
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
}

/* Glow pulse */
@keyframes glow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* Gradient shift */
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

## 5. Стили

### Tailwind конфигурация

```js
// tailwind.config.js extensions
{
  theme: {
    extend: {
      colors: {
        'bg-primary': '#0A0A0F',
        'bg-secondary': '#12121A',
        'bg-card': '#1A1A24',
        'accent-purple': '#8B5CF6',
        'accent-blue': '#3B82F6',
        'accent-pink': '#EC4899',
        'accent-cyan': '#06B6D4',
        'author-bg': '#F5F0E8',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 3s ease-in-out infinite',
        'gradient': 'gradientShift 8s ease infinite',
      }
    }
  }
}
```

### Глобальные стили

```css
/* index.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* {
  scroll-behavior: smooth;
}

body {
  background-color: #0A0A0F;
  color: #FFFFFF;
  font-family: 'Inter', system-ui, sans-serif;
}

/* Gradient text utility */
.gradient-text {
  background: linear-gradient(135deg, #8B5CF6, #3B82F6, #06B6D4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Glassmorphism */
.glass {
  background: rgba(26, 26, 36, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

## 6. SEO и мета-теги

```html
<!-- index.html -->
<title>KimiClaw — Ваш автономный AI-ассистент в облаке</title>
<meta name="description" content="OpenClaw as a Service на базе Kimi K2.5. Подключите почту, календарь, мессенджеры и получите компетентного помощника, который действует самостоятельно.">
<meta name="keywords" content="KimiClaw, OpenClaw, AI ассистент, Kimi K2.5, облачный сервис, автономный агент">

<!-- Open Graph -->
<meta property="og:title" content="KimiClaw — Ваш автономный AI-ассистент в облаке">
<meta property="og:description" content="OpenClaw as a Service на базе Kimi K2.5">
<meta property="og:type" content="website">
<meta property="og:url" content="https://www.kimi.com">

<!-- Twitter -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="KimiClaw — OpenClaw as a Service">
<meta name="twitter:description" content="Ваш автономный AI-ассистент в облаке">
```

## 7. Accessibility

- Semantic HTML (header, main, section, footer)
- ARIA labels для кнопок и ссылок
- Alt текст для изображений
- Keyboard navigation (tabindex)
- Focus visible states
- prefers-reduced-motion поддержка
- Контрастность текста минимум 4.5:1

## 8. Performance

- Lazy loading для изображений
- Code splitting (Vite автоматический)
- Оптимизированные шрифты (font-display: swap)
- Минимизация CSS/JS в production
- Tree shaking для неиспользуемого кода
