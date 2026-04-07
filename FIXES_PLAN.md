# План исправления ошибок Dokku PaaS Server

## Фаза 1: Критические исправления (CRITICAL) ✅
- [x] Исправить NPM уязвимости
- [x] Исправить Math.random() в sidebar.tsx
- [x] Исправить canonical URL и meta-теги
- [x] Исправить components.json

## Фаза 2: Исправления Ansible
- [ ] Исправить creates путь для Dokku
- [ ] Добавить проверку dist перед деплоем
- [ ] Исправить AIDE конфигурацию (verbose → report_level)
- [ ] Добавить SSL autorenew cron в Ansible

## Фаза 3: Документация
- [ ] Обновить AI_AGENT_DEPLOY_GUIDE.md
- [ ] Добавить .env.example
- [ ] Обновить AGENTS.md
- [ ] Создать эксплуатационную документацию (OPERATIONS.md)

## Фаза 4: Тестовый деплой
- [ ] Создать hello-world приложение
- [ ] Задеплоить через git push
- [ ] Проверить SSL
- [ ] Задокументировать процесс

## Фаза 5: Верификация
- [ ] Проверить все cron задачи
- [ ] Проверить Telegram уведомления
- [ ] Проверить CrowdSec работу
- [ ] Финальное тестирование
