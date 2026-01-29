
# app/services/email_service.py

# Placeholder para serviço de e-mail.
# Pode usar fastapi-mail ou smtplib aqui.

class EmailService:
    async def send_notification(self, email_to: str, subject: str, message: str):
        # TODO: Implementar envio real de email
        print(f"--- EMAIL SIMULADA ---")
        print(f"Para: {email_to}")
        print(f"Assunto: {subject}")
        print(f"Mensagem: {message}")
        print(f"----------------------")
        return True
