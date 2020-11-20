# LABA 2
Вариант 2

Программа позволяет создавать учетную запись, входить в учетную запись и выходить из нее. При авторизации осуществляется перевод на страницу с приветствием пользователя.

![](image (1).gif)

# Использование
Для запуска приложения необходимо:
1. В директории LR2 активировать virtualenv

`python -m venv env`

`.\env\Scripts\activate.bat`

2. Обновить версию pip

`python -m pip install --upgrade pip`

3. Установить зависимости из файла requirments.txt

`pip install -r requirements.txt`

4. Задать переменные окружения:

`set MAIL_USERNAME=your@gmail.com` (для отправления писем с этого аккаунта)

`set MAIL_PASSWORD=password` (пароль от почты)

`set FLASK_APP=MailAuth` (для указания запускаемого проекта)

5. Запустить flask

`flask run`



