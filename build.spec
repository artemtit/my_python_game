# Перейдите в папку проекта
cd C:\Users\titiv\OneDrive\Desktop\game

# Проверьте наличие иконки
if (!(Test-Path "icon.ico")) {
    Write-Host "Создайте файл icon.ico и поместите в эту папку"
    exit
}

# Запустите сборку
& "C:\Users\titiv\AppData\Local\Programs\Python\Python312\python.exe" -m PyInstaller `
    --onefile `
    --windowed `
    --noconsole `
    --icon="$pwd\icon.ico" `
    --add-data "*.png;assets" `
    --add-data "*.jpg;assets" `
    --add-data "*.mp3;assets" `
    main_pk.py