#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Скрипт для исправления проблем с кодировкой в файлах Python.
Удаляет нулевые байты и проблемные символы кодировки.
"""

import os
import sys

def fix_file_encoding(filename):
    """Исправляет проблемы с кодировкой в файле."""
    
    print(f"Обрабатываю файл: {filename}")
    
    try:
        # Открываем файл в бинарном режиме
        with open(filename, 'rb') as f:
            content = f.read()
        
        # Удаляем нулевые байты
        clean_content = content.replace(b'\x00', b'')
        
        # Удаляем BOM-маркеры
        if clean_content.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
            clean_content = clean_content[3:]
        elif clean_content.startswith(b'\xff\xfe') or clean_content.startswith(b'\xfe\xff'):  # UTF-16 BOM
            clean_content = clean_content[2:]
        
        # Проверяем, были ли изменения
        if content != clean_content:
            # Преобразуем в текст и записываем обратно
            try:
                # Сначала пробуем декодировать как UTF-8
                text = clean_content.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                # Если не получилось, пробуем другие кодировки
                try:
                    text = clean_content.decode('cp1251', errors='ignore')
                except UnicodeDecodeError:
                    text = clean_content.decode('latin-1', errors='ignore')
            
            # Запись в файл с правильной кодировкой
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"✅ Файл исправлен: {filename}")
        else:
            print(f"✓ Файл не требует изменений: {filename}")
        
        return True
    
    except Exception as e:
        print(f"❌ Ошибка при обработке файла {filename}: {e}")
        return False

def process_directory(directory, extensions=['.py']):
    """Обрабатывает все файлы с указанными расширениями в директории и её поддиректориях."""
    
    processed = 0
    success = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Проверяем расширение файла
            if any(file.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, file)
                processed += 1
                if fix_file_encoding(filepath):
                    success += 1
    
    return processed, success

def main():
    # Определяем директорию проекта
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = '.'
    
    print(f"Исправление проблем с кодировкой в директории: {os.path.abspath(project_dir)}")
    
    # Обрабатываем все Python файлы
    total, fixed = process_directory(project_dir)
    
    print("\nОбработка завершена!")
    print(f"Всего обработано файлов: {total}")
    print(f"Исправлено файлов: {fixed}")
    
    # Специально обрабатываем проблемное приложение messages_api, если оно существует
    messages_api_dir = os.path.join(project_dir, 'messages_api')
    if os.path.exists(messages_api_dir):
        print("\nДополнительная проверка файлов в приложении messages_api")
        specific_files = [
            os.path.join(messages_api_dir, 'views.py'),
            os.path.join(messages_api_dir, '__init__.py'),
            os.path.join(messages_api_dir, 'models.py'),
            os.path.join(messages_api_dir, 'serializers.py'),
            os.path.join(messages_api_dir, 'admin.py'),
            os.path.join(messages_api_dir, 'apps.py')
        ]
        
        for file in specific_files:
            if os.path.exists(file):
                fix_file_encoding(file)

if __name__ == "__main__":
    main() 