import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import settings

async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    try:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"[!] SMTP не настроен. Email НЕ отправлен на {to_email}")
            print(f"    Тема: {subject}")
            print(f"📄 Содержимое:\n{html_content}")
            return False
        
        message = MIMEMultipart("alternative")
        message["From"] = settings.SMTP_FROM or settings.SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )
        
        print(f"[+] Email успешно отправлен на {to_email}")
        return True
        
    except Exception as e:
        print(f"Ошибка отправки email на {to_email}: {str(e)}")
        return False

async def send_verification_code(email: str, code: str) -> bool:
    subject = "Код подтверждения регистрации"
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .code {{
                    font-size: 32px;
                    font-weight: bold;
                    color: #4a90e2;
                    text-align: center;
                    padding: 20px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    letter-spacing: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Подтверждение регистрации</h2>
                <p>Спасибо за регистрацию! Ваш код подтверждения:</p>
                <div class="code">{code}</div>
                <p>Введите этот код на странице регистрации для завершения процесса.</p>
                <p>Код действителен в течение 10 минут.</p>
                <div class="footer">
                    <p>Если вы не регистрировались на нашем сайте, просто проигнорируйте это письмо.</p>
                </div>
            </div>
        </body>
    </html>
    """
    
    return await send_email(email, subject, html_content)

async def send_welcome_email(email: str, username: str) -> bool:
    subject = "Добро пожаловать!"
    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Добро пожаловать, {username}!</h2>
                <p>Ваша регистрация успешно завершена.</p>
                <p>Теперь вы можете войти в систему и пользоваться всеми возможностями нашего сервиса.</p>
            </div>
        </body>
    </html>
    """
    
    return await send_email(email, subject, html_content)
