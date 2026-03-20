#!/usr/bin/env python3
"""
Database backup script - создаёт резервные копии базы данных
Запускается автоматически каждый день и вручную по команде
"""

import shutil
import os
import sys
from datetime import datetime

# Пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'bottega.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')
RETENTION_DAYS = 7  # Хранить бэкапы за 7 дней


def create_backup():
    """Создать резервную копию базы данных"""
    
    # Проверяем существование базы
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return None
    
    # Создаём папку для бэкапов
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Имя файла с датой
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'bottega_backup_{timestamp}.db')
    
    # Копируем базу
    shutil.copy2(DB_PATH, backup_file)
    
    # Получаем размер
    db_size = os.path.getsize(DB_PATH)
    backup_size = os.path.getsize(backup_file)
    
    print(f"✅ Backup created: {backup_file}")
    print(f"📊 Database size: {db_size} bytes")
    print(f"📦 Backup size: {backup_size} bytes")
    
    # Удаляем старые бэкапы
    cleanup_old_backups()
    
    return backup_file


def cleanup_old_backups():
    """Удалить бэкапы старше RETENTION_DAYS дней"""
    
    if not os.path.exists(BACKUP_DIR):
        return
    
    deleted_count = 0
    for filename in os.listdir(BACKUP_DIR):
        if filename.startswith('bottega_backup_') and filename.endswith('.db'):
            filepath = os.path.join(BACKUP_DIR, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            age = datetime.now() - file_mtime
            
            if age.days > RETENTION_DAYS:
                os.remove(filepath)
                deleted_count += 1
                print(f"🗑️ Deleted old backup: {filename}")
    
    if deleted_count > 0:
        print(f"📋 Deleted {deleted_count} old backup(s)")


if __name__ == '__main__':
    create_backup()
