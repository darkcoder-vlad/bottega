# БОТТЕГА квест — Telegram Bot для программы лояльности

Бот для программы лояльности ресторана: **9 визитов за 60 дней → 10-й визит бесплатно**

---

## 📋 Оглавление

- [Возможности](#-возможности)
- [Быстрый старт](#-быстрый-старт)
- [Настройка](#-настройка)
- [Деплой на сервер](#-деплой-на-сервер)
- [Запуск и управление](#-запуск-и-управление)
- [Команды администратора](#-команды-администратора)
- [Структура проекта](#-структура-проекта)
- [Решение проблем](#-решение-проблем)

---

## 🎯 Возможности

### Для гостей:
- Регистрация по номеру телефона
- Отслеживание прогресса (визиты, дни до конца цикла)
- Загрузка чеков для зачёта визитов
- Получение уникального кода награды
- Уведомления о прогрессе и истечении цикла

### Для администраторов:
- Подтверждение/отклонение чеков
- Просмотр информации о пользователях
- Статистика программы
- Отметка использованных наград
- Массовая рассылка

### Антифрод:
- Максимум 1 визит в сутки
- Проверка чеков администратором
- Минимальная сумма чека (3000 ₽)
- Уникальные коды наград
- Срок действия цикла (60 дней)

---

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd /path/to/bottega
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
nano .env  # или ваш редактор
```

Заполните `.env`:
- `BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS` — ваши Telegram ID (узнать через [@userinfobot](https://t.me/userinfobot))

### 3. Запуск

```bash
python main.py
```

---

## 🖥️ Деплой на сервер

### Требования
- Ubuntu/Debian Linux
- Python 3.8+
- Доступ к интернету (для Telegram API)

---

### Вариант 1: systemd (рекомендуется)

#### Шаг 1: Подготовка сервера

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

#### Шаг 2: Создание пользователя

```bash
sudo useradd -r -m -s /bin/bash bottega
```

#### Шаг 3: Загрузка проекта

```bash
sudo -i -u bottega
cd /home/bottega
git clone <repository_url> bottega  # или загрузите файлы через SCP/SFTP
cd bottega
```

Или загрузите файлы напрямую:

```bash
# На локальной машине
tar -czf bottega.tar.gz main.py requirements.txt .env.example README.md bottega_hub/
scp bottega.tar.gz bottega@your_server:/home/bottega/

# На сервере
sudo -i -u bottega
cd /home/bottega
tar -xzf bottega.tar.gz
rm bottega.tar.gz
```

#### Шаг 4: Установка зависимостей

```bash
cd /home/bottega/bottega
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Шаг 5: Настройка окружения

```bash
cp .env.example .env
nano .env
```

Заполните:
```env
BOT_TOKEN=ваш_токен_от_BotFather
ADMIN_IDS=ваш_telegram_id
DATABASE_PATH=bottega_hub/data/bottega.db
MIN_CHECK_AMOUNT=3000
VISITS_REQUIRED=9
CYCLE_DAYS=60
MAX_REWARD_AMOUNT=3000
INACTIVE_DAYS_NOTIFY=7
```

#### Шаг 6: Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/bottega-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=BOTTEGA квест — Loyalty Program Bot
After=network.target

[Service]
Type=simple
User=bottega
Group=bottega
WorkingDirectory=/home/bottega/bottega
Environment="PATH=/home/bottega/bottega/venv/bin"
ExecStart=/home/bottega/bottega/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bottega-bot

[Install]
WantedBy=multi-user.target
```

#### Шаг 7: Запуск сервиса

```bash
sudo systemctl daemon-reload
sudo systemctl enable bottega-bot
sudo systemctl start bottega-bot
sudo systemctl status bottega-bot
```

---

### Вариант 2: Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: bottega-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./bottega_hub/data:/app/bottega_hub/data
      - ./bottega_hub/logs:/app/bottega_hub/logs
```

#### Запуск

```bash
docker-compose up -d
docker-compose logs -f
```

---

### Вариант 3: nohup (для тестирования)

```bash
cd /home/bottega/bottega
source venv/bin/activate
nohup python main.py > bottega_hub/logs/bot.log 2>&1 &

# Проверка
ps aux | grep main.py
```

---

## 🔧 Запуск и управление

### systemd команды

```bash
# Статус
sudo systemctl status bottega-bot

# Просмотр логов
sudo journalctl -u bottega-bot -f

# Перезапуск
sudo systemctl restart bottega-bot

# Остановка
sudo systemctl stop bottega-bot

# Старт
sudo systemctl start bottega-bot

# Отключить автозапуск
sudo systemctl disable bottega-bot
```

### Проверка работы

```bash
# Процесс запущен
ps aux | grep main.py

# Порт не нужен (бот использует long polling)
# Проверка связи с Telegram
curl -s https://api.telegram.org/bot<BOT_TOKEN>/getMe
```

---

## 👨‍💼 Команды администратора

| Команда | Описание |
|---------|----------|
| `/stats` | Статистика программы |
| `/user <телефон\|ID>` | Информация о пользователе |
| `/reward_used <код>` | Отметить награду использованной |
| `/broadcast <текст>` | Массовая рассылка |

### Примеры

```bash
# Статистика
/stats

# Информация о пользователе по телефону
/user 79991234567

# Информация по внутреннему ID
/user 12345

# Отметить награду
/reward_used BTG-9384-KQ

# Рассылка
/broadcast Уважаемые гости! Мы запустили новую программу лояльности!
```

---

## 📁 Структура проекта

```
bottega/
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── .env                    # Конфигурация (не хранить в git!)
├── .env.example           # Шаблон конфигурации
├── README.md              # Документация
│
└── bottega_hub/
    ├── bot/
    │   ├── handlers/      # Обработчики сообщений
    │   │   ├── admin.py
    │   │   ├── checkin.py
    │   │   ├── menu.py
    │   │   ├── progress.py
    │   │   ├── reward.py
    │   │   ├── rules.py
    │   │   ├── start.py
    │   │   └── support.py
    │   ├── keyboards/     # Клавиатуры
    │   ├── middlewares/   # Middleware (БД, логирование)
    │   ├── utils/         # Утилиты
    │   ├── dispatcher.py  # Настройка бота
    │   └── notifications.py # Уведомления
    ├── config/            # Конфигурация приложения
    ├── database/          # Работа с БД
    │   ├── database.py
    │   └── repositories.py
    ├── models/            # SQLAlchemy модели
    │   ├── user.py
    │   ├── visit.py
    │   ├── receipt.py
    │   ├── reward.py
    │   └── consent.py
    ├── data/              # SQLite база данных
    │   └── bottega.db
    └── logs/              # Логи (создаётся при запуске)
        └── bot.log
```

---

## 🔐 Безопасность

### .env файл
- **Никогда не коммитьте `.env` в git**
- Добавьте `.env` в `.gitignore`
- Храните токен бота в секрете

### Доступы
- Ограничьте доступ к серверу по SSH
- Используйте отдельного пользователя для бота
- Настройте firewall (UFW)

```bash
sudo ufw allow ssh
sudo ufw enable
```

---

## 🐛 Решение проблем

### Бот не запускается

1. Проверьте токен:
```bash
curl -s https://api.telegram.org/bot<BOT_TOKEN>/getMe
```

2. Проверьте логи:
```bash
sudo journalctl -u bottega-bot -f
```

3. Проверьте права доступа:
```bash
ls -la /home/bottega/bottega/
```

### Пользователи не могут зачесть визит

1. Проверьте, что администраторы подтверждают чеки
2. Проверьте минимальную сумму чека (3000 ₽)
3. Проверьте логи на наличие ошибок

### Бот упал и не перезапускается

```bash
# Перезапуск сервиса
sudo systemctl restart bottega-bot

# Проверка статуса
sudo systemctl status bottega-bot

# Если не помогает — проверьте логи
sudo journalctl -u bottega-bot -n 100
```

### Ошибки базы данных

```bash
# Проверка целостности БД
sqlite3 bottega_hub/data/bottega.db "PRAGMA integrity_check;"

# Резервное копирование
cp bottega_hub/data/bottega.db bottega_hub/data/bottega.db.backup
```

---

## 📊 Мониторинг

### Логирование

Логи пишутся в:
- `bottega_hub/logs/bot.log` — логи приложения
- `journalctl -u bottega-bot` — системные логи (при использовании systemd)

### Метрики для отслеживания

- Количество зарегистрированных пользователей
- Количество активных циклов
- Среднее время до завершения цикла
- Количество выданных наград

---

## 📞 Поддержка

- 📱 Телефон: +7 (931) 994-75-02
- 📧 Email: gtn@bottega.city
- 💬 Telegram: @wexion (разработчик)

---

## 📄 Лицензия

Проект создан для внутреннего использования БОТТЕГА квест.

**Автор кода:** @wexion
