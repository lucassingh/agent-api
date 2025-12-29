import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import secrets
from ..core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.emails_from_email = settings.EMAILS_FROM_EMAIL
    
    def send_email(
        self, 
        email_to: str, 
        subject: str, 
        body: str,
        body_html: Optional[str] = None
    ) -> bool:
        if not self.smtp_host:
            print(f"Email would be sent to {email_to}: {subject}")
            print(f"Body: {body}")
            return True
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.emails_from_email
        msg["To"] = email_to
        
        part1 = MIMEText(body, "plain")
        msg.attach(part1)
        
        if body_html:
            part2 = MIMEText(body_html, "html")
            msg.attach(part2)
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_verification_email(self, email_to: str, verification_code: str) -> bool:
        subject = "Verify your email - Agent API"
        body = f"""
        Welcome to Agent API!
        
        Please use the following code to verify your email: {verification_code}
        
        This code will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        body_html = f"""
        <html>
            <body>
                <h2>Welcome to Agent API!</h2>
                <p>Please use the following code to verify your email:</p>
                <h3>{verification_code}</h3>
                <p>This code will expire in 24 hours.</p>
                <p>If you didn't create an account, please ignore this email.</p>
            </body>
        </html>
        """
        
        return self.send_email(email_to, subject, body, body_html)
    
    def send_password_reset_email(self, email_to: str, reset_token: str) -> bool:
        subject = "Password Reset - Agent API"
        body = f"""
        You requested a password reset for your Agent API account.
        
        Please use the following token to reset your password: {reset_token}
        
        This token will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email.
        """
        
        body_html = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested a password reset for your Agent API account.</p>
                <p>Please use the following token to reset your password:</p>
                <h3>{reset_token}</h3>
                <p>This token will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
            </body>
        </html>
        """
        
        return self.send_email(email_to, subject, body, body_html)


def generate_verification_code() -> str:
    return secrets.token_hex(3).upper()  # 6 character code


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


email_service = EmailService()