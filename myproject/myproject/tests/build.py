import os
import shutil
import subprocess
import sys
import zipfile

def create_zip_archive():
    """Создаёт ZIP-архив с игрой"""
    print("Создание ZIP-архива...")
    try:
        with zipfile.ZipFile('PixelHopperPro.zip', 'w') as zipf:
            # Добавляем EXE-файл
            if os.path.exists('dist/main_pk.exe'):
                zipf.write('dist/main_pk.exe', 'PixelHopperPro.exe')
            
            # Добавляем assets
            assets_dir = 'assets'
            if os.path.exists(assets_dir):
                for root, dirs, files in os.walk(assets_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, start='.')
                        zipf.write(file_path, arcname)
        
        print("ZIP-архив успешно создан: PixelHopperPro.zip")
        return True
    except Exception as e:
        print(f"Ошибка при создании ZIP-архива: {e}")
        return False

def build():
    """Основная функция сборки"""
    try:
        # 1. Сборка PyInstaller
        print("Запуск PyInstaller...")
        subprocess.run([
            "pyinstaller",
            "--onefile",
            "--windowed",
            "--noconsole",
            "--icon=icon.ico",
            "--add-data", "*.png;assets",
            "--add-data", "*.jpg;assets",
            "--add-data", "*.mp3;assets",
            "main_pk.py"
        ], check=True)

        # 2. Копирование ресурсов
        print("Копирование ресурсов...")
        os.makedirs("dist/assets", exist_ok=True)
        for file in os.listdir("."):
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".mp3", ".wav")):
                shutil.copy2(file, "dist/assets")

        # 3. Попытка создания установщика Inno Setup
        inno_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        if os.path.exists(inno_path):
            print("Найден Inno Setup, создаём установщик...")
            try:
                subprocess.run([inno_path, "installer.iss"], check=True)
                print("Установщик создан успешно!")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Ошибка Inno Setup: {e}")
                return create_zip_archive()
        else:
            print("Inno Setup не найден")
            return create_zip_archive()

    except Exception as e:
        print(f"Критическая ошибка сборки: {e}")
        return False

if __name__ == "__main__":
    print("=== Начало процесса сборки ===")
    if build():
        print("=== Сборка успешно завершена ===")
        sys.exit(0)
    else:
        print("=== Сборка завершена с ошибками ===")
        sys.exit(1)