# Аудит проекта Dokku PaaS Server

**Дата аудита:** 2026-04-07  
**Аудитор:** AI Agent  
**Статус:** ⚠️ Требуется внимание

---

## 1. Общая информация о проекте

| Параметр | Значение |
|----------|----------|
| **Проект** | Dokku PaaS Server с Landing Page |
| **Стек** | Ansible, React 19 + TypeScript, Vite, Tailwind CSS, shadcn/ui |
| **Сервер** | clawtech.ru (31.177.83.27) |
| **SSH порт** | 2233 |

---

## 2. Критические проблемы 🔴

### 2.1 Уязвимости безопасности NPM (HIGH)

**Статус:** 8 уязвимостей (2 moderate, 6 high)

| Пакет | Уязвимость | CVE | Уровень |
|-------|------------|-----|---------|
| `vite` 7.0.0-7.3.1 | Path Traversal | GHSA-4w7w-66w2-5vf9, GHSA-v2wj-q39q-566r, GHSA-p9ff-h696-f583 | HIGH |
| `rollup` 4.0.0-4.58.0 | Arbitrary File Write | GHSA-mw96-cpmx-2vgc | HIGH |
| `lodash` ≤4.17.23 | Prototype Pollution, Code Injection | GHSA-xxjr-mmjv-4gpg, GHSA-r5fr-rjxr-66jc, GHSA-f23m-r3pf-42rh | HIGH |
| `minimatch` ≤3.1.3 | ReDoS | GHSA-3ppc-4f35-3m26, GHSA-7r86-cg39-jmmj, GHSA-23c5-xmqv-rm74 | HIGH |
| `picomatch` ≤2.3.1 | Method Injection, ReDoS | GHSA-3v7f-55p6-f55p, GHSA-c2c7-rcm5-vvqj | HIGH |
| `flatted` ≤3.4.1 | Prototype Pollution, DoS | GHSA-25h7-pfq9-p65f, GHSA-rf6f-7fwh-wjgh | HIGH |
| `ajv` <6.14.0 | ReDoS | GHSA-2g4f-4pwh-qvx6 | MODERATE |
| `brace-expansion` <1.1.13 или 2.0.0-2.0.3 | Zero-step sequence | GHSA-f886-m6hf-6m8v | MODERATE |

**Рекомендация:**
```bash
cd landing/app
npm audit fix
# Или для принудительного исправления:
npm audit fix --force
```

---

## 3. Ошибки ESLint (React) 🟡

### 3.1 Ошибка чистоты компонента (CRITICAL)

**Файл:** `landing/app/src/components/ui/sidebar.tsx:611`

```tsx
// ❌ НЕПРАВИЛЬНО - Math.random() в рендере нарушает чистоту
const width = React.useMemo(() => {
  return `${Math.floor(Math.random() * 40) + 50}%`
}, [])
```

**Проблема:** `Math.random()` — импурная функция. React требует, чтобы компоненты были чистыми (idempotent). При re-render компонента будут получены разные значения, что может привести к непредсказуемому поведению и hydration mismatch в SSR.

**Исправление:**
```tsx
// ✅ ПРАВИЛЬНО - Стабильное значение через сид
const width = React.useMemo(() => {
  // Используем хеш от className или другой стабильный источник
  const seed = className?.length || 0;
  return `${50 + (seed % 40)}%`;
}, [className]);

// Или использовать CSS-only решение без JS random
```

### 3.2 Ошибки Fast Refresh (7 шт.)

**Правило:** `react-refresh/only-export-components`

**Проблема:** Fast Refresh работает только когда файл экспортирует исключительно компоненты React. Экспорт вспомогательных функций/констант нарушает горячую перезагрузку.

**Файлы с ошибками:**

| Файл | Строка | Экспорт |
|------|--------|---------|
| `badge.tsx` | 46 | `badgeVariants` |
| `button-group.tsx` | 82 | `ButtonGroup` (named export вместе с default) |
| `button.tsx` | 62 | `buttonVariants` |
| `form.tsx` | 159 | `Form`, `FormItem`, `FormLabel` и др. |
| `navigation-menu.tsx` | 167 | `NavigationMenuList`, `NavigationMenuItem` и др. |
| `sidebar.tsx` | 725 | `Sidebar`, `SidebarContent` и др. |
| `toggle.tsx` | 45 | `toggleVariants` |

**Рекомендации:**

1. **Для вариантов (variants):** Вынести в отдельный файл или использовать type-only exports
```tsx
// ✅ Решение: Разделить на два файла
// button-variants.ts
export const buttonVariants = cva(...);

// button.tsx
import { buttonVariants } from './button-variants';
export { Button };
```

2. **Для множественных компонентов:** Каждый компонент в отдельном файле
```tsx
// ✅ Решение: Один компонент = один файл
// NavigationMenu/index.tsx → экспортирует только NavigationMenu
// NavigationMenuList.tsx → отдельный файл
```

3. **Или отключить правило для UI компонентов** (не рекомендуется):
```js
// eslint.config.js
{
  files: ['src/components/ui/**/*.tsx'],
  rules: {
    'react-refresh/only-export-components': 'off'
  }
}
```

---

## 4. Проблемы конфигурации 🟡

### 4.1 Конфигурация shadcn/ui

**Файл:** `landing/app/components.json`

```json
{
  "tailwind": {
    "config": "postcss.config.js"  // ❌ Должно быть "tailwind.config.js"
  }
}
```

**Проблема:** Указан путь к `postcss.config.js` вместо `tailwind.config.js`. Это может вызывать проблемы при обновлении компонентов через CLI shadcn.

**Исправление:**
```json
{
  "tailwind": {
    "config": "tailwind.config.js"
  }
}
```

### 4.2 Отсутствует .env.example

**Проблема:** В проекте используется `TELEGRAM_BOT_TOKEN` как environment variable, но нет примера файла `.env.example` для документирования требуемых переменных.

**Рекомендация:** Создать `landing/app/.env.example`:
```bash
# Для разработки (опционально)
VITE_API_URL=

# Для Ansible (обязательно)
TELEGRAM_BOT_TOKEN=
```

---

## 5. Проблемы Ansible 🟡

### 5.1 Потенциальная проблема с handlers

**Файл:** `ansible/site.yml`

```yaml
- name: Restart SSH immediately
  meta: flush_handlers
```

**Примечание:** Handler `restart ssh` использует `name: ssh`, что верно для Ubuntu 24.04 (не `sshd`). Это корректно согласно AGENTS.md.

### 5.2 Отсутствие `creates` для некоторых задач

**Файл:** `ansible/roles/dokku-install/tasks/main.yml`

```yaml
- name: Download and install Dokku
  shell: |
    wget -qO- https://dokku.com/install.sh | bash
  args:
    creates: /usr/bin/dokku
```

**Проблема:** Dokku устанавливается в `/usr/local/bin/dokku`, но проверка `creates` на `/usr/bin/dokku`. В `site.yml` создается symlink, но это может привести к повторной установке.

**Исправление:**
```yaml
- name: Download and install Dokku
  shell: |
    wget -qO- https://dokku.com/install.sh | bash
  args:
    creates: /usr/local/bin/dokku  # Исправлен путь
```

### 5.3 Использование устаревшего модуля `apt_key`

**Файл:** `ansible/roles/crowdsec/tasks/main.yml`

```yaml
- name: Add CrowdSec GPG key
  apt_key:
    url: https://packagecloud.io/crowdsec/crowdsec/gpgkey
    state: present
```

**Примечание:** Модуль `apt_key` помечен как deprecated в новых версиях Ansible. Рекомендуется использовать `get_url` с сохранением в `/etc/apt/keyrings/`.

---

## 6. Проблемы SEO/Meta 🟡

### 6.1 Некорректный canonical URL

**Файл:** `landing/app/index.html` и `landing/app/dist/index.html`

```html
<link rel="canonical" href="https://www.kimi.com" />
```

**Проблема:** Указан URL `kimi.com`, но домен проекта `clawtech.ru`. Это может негативно повлиять на SEO.

**Исправление:**
```html
<link rel="canonical" href="https://clawtech.ru" />
```

### 6.2 Несоответствие доменов в meta

**Open Graph и Twitter meta tags** также содержат `kimi.com` вместо `clawtech.ru`.

---

## 7. Проблемы сборки и деплоя 🟡

### 7.1 Отсутствие проверки dist перед деплоем

**Файл:** `ansible/roles/landing/tasks/main.yml`

**Проблема:** Ansible задачи не проверяют существование `dist/` перед копированием. Если сборка не была выполнена, деплой завершится ошибкой.

**Рекомендация:** Добавить pre-flight check:
```yaml
- name: Check dist directory exists
  stat:
    path: "{{ playbook_dir }}/../landing/app/dist/index.html"
  delegate_to: localhost
  register: dist_index
  
- name: Fail if dist not built
  fail:
    msg: "Landing page dist not built. Run 'npm run build' first."
  when: not dist_index.stat.exists
```

### 7.2 Отсутствие .static файла

**Проблема:** В `dist/` присутствует файл `.static`, но это может конфликтовать с `static.json`. Для buildpack-nginx рекомендуется использовать только `static.json`.

---

## 8. Рекомендации по улучшению

### 8.1 Зависимости

- **React 19.2.0** — актуальная версия ✓
- **Vite 7.2.4** — требуется обновление до 7.4.0+ для исправления уязвимостей
- **TypeScript 5.9.3** — отлично, используется последняя версия ✓

### 8.2 Производительность

**Рекомендации:**
1. Добавить `vite-plugin-compression` для gzip/brotli сжатия
2. Настроить lazy loading для тяжелых компонентов (chart.tsx, calendar.tsx)
3. Оптимизировать изображение `hero-illustration.png` (2.5 MB — слишком большое)

```bash
# Проверка размера ресурсов
ls -lh landing/app/dist/assets/
# -rw-r--r-- 1 user staff 371K index-DxHiyHRM.js
# -rw-r--r-- 1 user staff 2.5M hero-illustration.png ⚠️
```

### 8.3 Доступность (Accessibility)

**Замечания:**
- В `Hero.tsx` отсутствует `alt` текст для декоративных элементов — корректно
- Навигация имеет `aria-label` — отлично ✓
- Темная/светлая тема переключается корректно ✓

### 8.4 Тестирование

**Отсутствует:**
- Unit тесты (Jest/Vitest)
- E2E тесты (Playwright/Cypress)
- Visual regression тесты

**Рекомендация:** Добавить минимальный набор тестов:
```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

---

## 9. Сводка по приоритетам

| Приоритет | Задача | Файлы |
|-----------|--------|-------|
| 🔴 **CRITICAL** | Исправить уязвимости NPM | `package.json`, `package-lock.json` |
| 🔴 **CRITICAL** | Исправить Math.random() в sidebar | `src/components/ui/sidebar.tsx` |
| 🟡 **HIGH** | Исправить canonical URL | `index.html` |
| 🟡 **HIGH** | Обновить shadcn config | `components.json` |
| 🟡 **MEDIUM** | Исправить ESLint ошибки | `src/components/ui/*.tsx` |
| 🟡 **MEDIUM** | Исправить creates в Ansible | `roles/dokku-install/tasks/main.yml` |
| 🟢 **LOW** | Добавить .env.example | новый файл |
| 🟢 **LOW** | Оптимизировать изображения | `public/hero-illustration.png` |

---

## 10. Быстрые команды для исправления

```bash
# 1. Исправить уязвимости
cd landing/app && npm audit fix

# 2. Проверить сборку
npm run build

# 3. Проверить линтер
npm run lint

# 4. Синтаксическая проверка Ansible
cd ../../ansible
ansible-playbook -i inventory.ini site.yml --syntax-check

# 5. Dry-run Ansible (без изменений)
ansible-playbook -i inventory.ini site.yml --check
```

---

## Выводы

Проект в целом **стабилен и работоспособен**, но требует внимания к:

1. **Безопасности** — 6 high severity уязвимостей в зависимостях
2. **Корректности React** — ошибка с Math.random() может вызвать проблемы
3. **SEO** — неверный canonical URL

Ansible конфигурация синтаксически корректна и готова к деплою после исправления мелких замечаний.

---

*Аудит выполнен с использованием:*
- ESLint 9 с react-refresh плагином
- npm audit
- Ansible --syntax-check
- Context7 (React документация)
