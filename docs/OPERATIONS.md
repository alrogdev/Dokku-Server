# Эксплуатационная документация Dokku PaaS Server

**Сервер:** clawtech.ru (31.177.83.27)  
**SSH порт:** 2233  
**Последнее обновление:** 2026-04-07

---

## Содержание

1. [Обзор системы](#обзор-системы)
2. [Ежедневные операции](#ежедневные-операции)
3. [Мониторинг и алерты](#мониторинг-и-алерты)
4. [Резервное копирование](#резервное-копирование)
5. [Обновление системы](#обновление-системы)
6. [Решение проблем](#решение-проблем)
7. [Аварийное восстановление](#аварийное-восстановление)

---

## Обзор системы

### Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    SpaceWeb VPS (31.177.83.27)              │
│                    Ubuntu 24.04 LTS                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  CIS Level 1 │  │    Dokku     │  │   CrowdSec       │  │
│  │  Hardening   │  │  (Docker)    │  │  + Telegram      │  │
│  │              │  │              │  │  + CAPI          │  │
│  │  • SSH 2233  │  │  • Node.js   │  │  • nftables      │  │
│  │  • nftables  │  │  • Python    │  │  • Docker        │  │
│  │  • Auditd    │  │  • PG/Redis  │  │                  │  │
│  │  • AIDE      │  │  • Nginx     │  │                  │  │
│  │  • Lynis     │  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Мониторинг (Cron)                        │ │
│  │  • AIDE: 23:00 ежедневно                              │ │
│  │  • Lynis: 00:00 воскресенье                           │ │
│  │  • CrowdSec: каждые 6 часов                           │ │
│  │  • SSL: 02:00 ежедневно                               │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Компоненты системы

| Компонент | Версия | Назначение | Статус |
|-----------|--------|------------|--------|
| **Dokku** | 0.37.7 | PaaS платформа | ✅ |
| **Docker** | 28.2.2 | Контейнеризация | ✅ |
| **CrowdSec** | 1.7.7 | IDS/IPS | ✅ |
| **AIDE** | 0.18.6 | FIM мониторинг | ✅ |
| **Lynis** | 3.0.8 | Аудит безопасности | ✅ |
| **nftables** | 1.0.9 | Firewall | ✅ |

---

## Ежедневные операции

### Утренняя проверка (рекомендуется)

```bash
# Подключение к серверу
ssh -p 2233 -i .opencode/openwork/inbox/PETS-keys root@31.177.83.27

# Проверка статуса системы
echo "=== Система ===" && uptime
echo "=== Диск ===" && df -h / | tail -1
echo "=== Память ===" && free -h | grep Mem

# Проверка CrowdSec
echo "=== CrowdSec ===" && cscli metrics | head -20

# Проверка приложений
echo "=== Dokku Apps ===" && dokku apps:list
dokku ps:report landing
```

### Проверка логов

```bash
# Логи системы
journalctl -xe | tail -50

# Логи CrowdSec
journalctl -u crowdsec -n 100

# Логи приложения
 dokku logs landing -n 100
```

---

## Мониторинг и алерты

### Telegram бот

**Бот:** @Rogdev_Sec_alert_bot  
**Chat ID:** 1631006

**Типы уведомлений:**
- 🚨 **AIDE Alert** - Обнаружены изменения файлов
- 🔒 **Lynis Audit** - Результаты аудита безопасности
- 🛡️ **CrowdSec Report** - Статистика атак

### Cron расписание

```bash
# Проверка всех задач
crontab -l

# Текущие задачи:
# 0 23 * * *   - AIDE проверка целостности
# 0 00 * * 0   - Lynis аудит (воскресенье)
# */6 * * * *  - CrowdSec отчет
# 0 2 * * *    - SSL обновление
```

### Ручная проверка мониторинга

```bash
# AIDE - проверка целостности
aide -c /etc/aide/aide.conf --check

# Lynis - аудит безопасности
lynis audit system --quick

# CrowdSec - метрики
cscli metrics
cscli decisions list

# Проверка SSL
openssl s_client -connect clawtech.ru:443 -servername clawtech.ru < /dev/null 2>/dev/null | openssl x509 -noout -dates
```

---

## Резервное копирование

### Что бэкапить

**Критично:**
- `/home/dokku/` - Приложения и данные Dokku
- `/var/lib/dokku/` - Конфигурация Dokku
- `/var/lib/aide/aide.db` - База AIDE
- `/etc/crowdsec/` - Конфигурация CrowdSec
- SSH ключи: `.opencode/openwork/inbox/PETS-keys`

**Важно:**
- PostgreSQL базы данных
- Redis данные
- Persistent storage приложений

### Создание бэкапа

```bash
#!/bin/bash
# backup.sh - Резервное копирование

BACKUP_DIR="/backup/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Бэкап Dokku
tar czf $BACKUP_DIR/dokku-config.tar.gz /home/dokku/ /var/lib/dokku/

# Бэкап AIDE
cp /var/lib/aide/aide.db $BACKUP_DIR/

# Бэкап CrowdSec
tar czf $BACKUP_DIR/crowdsec.tar.gz /etc/crowdsec/

# Бэкап баз данных
for db in $(dokku postgres:list | tail -n +2 | awk '{print $1}'); do
    dokku postgres:export $db > $BACKUP_DIR/postgres-$db.sql
done

# Синхронизация на удаленный сервер (пример)
# rsync -avz $BACKUP_DIR/ backup-server:/backups/clawtech/

echo "Backup completed: $BACKUP_DIR"
```

### Восстановление из бэкапа

```bash
# Восстановление Dokku
tar xzf backup/dokku-config.tar.gz -C /

# Восстановление базы данных
dokku postgres:import myapp-db < backup/postgres-myapp-db.sql

# Перезапуск приложений
dokku ps:restart --all
```

---

## Обновление системы

### Обновление пакетов безопасности

```bash
# Обновление только security-пакетов
apt-get update
apt-get -s upgrade | grep -i security
apt-get upgrade -y

# Перезагрузка если требуется
[ -f /var/run/reboot-required ] && reboot
```

### Обновление Dokku

```bash
# Обновление Dokku
dokku-update run

# Или вручную:
# wget -qO- https://dokku.com/install.sh | bash
```

### Обновление CrowdSec

```bash
# Обновление коллекций
cscli collections upgrade -a

# Обновление парсеров
cscli parsers upgrade -a

# Обновление сценариев
cscli scenarios upgrade -a

# Перезапуск
dokku ps:restart crowdsec
```

---

## Решение проблем

### SSH недоступен

```bash
# Через VNC консоль SpaceWeb:
# 1. Войти как root
# 2. Проверить SSH:
systemctl status ssh

# 3. Если нужно, временно открыть порт 22:
nft add rule inet filter input tcp dport 22 accept

# 4. Исправить конфигурацию SSH
vim /etc/ssh/sshd_config

# 5. Перезапустить SSH
systemctl restart ssh
```

### CrowdSec блокирует легитимный трафик

```bash
# Проверка заблокированных IP
cscli decisions list

# Временный whitelist IP (24 часа)
cscli decisions add -i IP_ADDRESS --duration 24h

# Постоянный whitelist (в конфиге)
vim /etc/crowdsec/parsers/s02-enrich/whitelist.yaml
```

### Проблемы с SSL сертификатом

```bash
# Проверка статуса
dokku letsencrypt:report landing

# Ручное обновление
dokku letsencrypt:auto-renew

# Пересоздание сертификата
dokku letsencrypt:disable landing
dokku letsencrypt:enable landing
```

### Приложение не запускается

```bash
# Проверка статуса
dokku ps:report myapp

# Просмотр логов
dokku logs myapp -n 200

# Пересборка
dokku ps:rebuild myapp

# Проверка конфигурации
dokku config:show myapp
```

---

## Аварийное восстановление

### Полная потеря сервера

1. **Создать новый VPS** с Ubuntu 24.04
2. **Обновить DNS** - изменить A-запись на новый IP
3. **Запустить Ansible:**
   ```bash
   cd ansible
   ansible-playbook -i inventory.ini site.yml
   ```
4. **Восстановить бэкапы:**
   - Приложения из git
   - Базы данных из SQL
   - Persistent storage из tar.gz
5. **Проверить SSL** - новые сертификаты будут созданы автоматически

### Контакты для экстренной помощи

- **Telegram:** @Rogdev
- **Бот уведомлений:** @Rogdev_Sec_alert_bot
- **VNC Console:** SpaceWeb личный кабинет

---

## Полезные команды

```bash
# Система
htop                    # Мониторинг ресурсов
ncdu /                  # Анализ использования диска
fail2ban-client status  # Статус fail2ban

# Docker
docker ps               # Список контейнеров
docker system prune     # Очистка неиспользуемых образов

# Dokku
dokku apps:list         # Список приложений
dokku ps:scale landing web=2  # Масштабирование
dokku enter landing     # Вход в контейнер

# Сеть
ss -tlnp                # Открытые порты
nft list ruleset        # Правила firewall
```

---

## Чеклист обслуживания

### Ежедневно:
- [ ] Проверить Telegram уведомления
- [ ] Проверить доступность сайта
- [ ] Проверить логи CrowdSec

### Еженедельно:
- [ ] Проверить использование диска
- [ ] Просмотреть отчет Lynis
- [ ] Обновить CrowdSec коллекции

### Ежемесячно:
- [ ] Создать полный бэкап
- [ ] Проверить срок действия SSL сертификатов
- [ ] Обзор безопасности (cscli metrics)
- [ ] Тестирование восстановления из бэкапа

---

*Документация создана: 2026-04-07*  
*Обновляется по мере изменений в системе*
