def clean_file(filename):
    with open(filename, 'rb') as f:
        content = f.read()
    
    # Удаление нулевых байтов
    clean_content = content.replace(b'\x00', b'')
    
    with open(filename, 'wb') as f:
        f.write(clean_content)
    
    print(f"Очищен файл: {filename}")

# Список файлов для очистки
files = [
    'messages_api/views.py',
    'messages_api/__init__.py',
    'messages_api/apps.py',
    'messages_api/admin.py',
    'messages_api/models.py',
    'messages_api/serializers.py'
]

for file in files:
    try:
        clean_file(file)
    except Exception as e:
        print(f"Ошибка при обработке {file}: {e}")