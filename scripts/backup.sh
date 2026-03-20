#!/bin/bash
# Ручной бэкап базы данных бота

PROJECT_DIR="/Users/vladislav/My projects/bottega"
DB_PATH="$PROJECT_DIR/bottega_hub/data/bottega.db"
BACKUP_DIR="$PROJECT_DIR/bottega_hub/backups"

# Создаём папку для бэкапов
mkdir -p "$BACKUP_DIR"

# Имя файла с датой
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bottega_backup_$TIMESTAMP.db"

# Проверяем существование базы
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found: $DB_PATH"
    exit 1
fi

# Копируем базу
cp "$DB_PATH" "$BACKUP_FILE"

# Получаем размер
DB_SIZE=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null)

echo "✅ Backup created: $BACKUP_FILE"
echo "📊 Database size: $DB_SIZE bytes"
echo "📦 Backup size: $BACKUP_SIZE bytes"

# Удаляем старые бэкапы (старше 7 дней)
find "$BACKUP_DIR" -name "bottega_backup_*.db" -mtime +7 -delete 2>/dev/null
echo "🗑️ Old backups cleaned (older than 7 days)"
