import os
from typing import Optional
from datetime import datetime
from logger_utils import logger

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

async def send_email(to_email: str, subject: str, body: str, html: bool = True) -> bool:
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def send_admin_notification(user_email: str, plan_type: str, user_status: str):
    subject = f"WelFore Health - {plan_type} Plan Delivered to {user_status} User"
    
    body = f"""
    <html>
    <body>
        <h2>Plan Delivery Notification</h2>
        <p><strong>User Email:</strong> {user_email}</p>
        <p><strong>Plan Type:</strong> {plan_type}</p>
        <p><strong>User Status:</strong> {user_status}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """
    
    await send_email(ADMIN_EMAIL, subject, body, html=True)

def get_free_plan_email(user_name: str = 'there') -> str:
    return f"""
    <html>
    <body>
        <h2>Your FREE 3-Day Meal Plan is Ready!</h2>
        <p>Hi {user_name},</p>
        <p>Thank you for completing the WelFore Health quiz! Your personalized 3-day meal plan has been created.</p>
        
        <h3>What's Next?</h3>
        <p>Love your results? Upgrade to get even more value:</p>
        <ul>
            <li><strong>7-Day Plan</strong> - More variety and flexibility 
                <a href="https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a">Get 7-Day Plan</a>
            </li>
            <li><strong>14-Day Plan</strong> - Complete meal planning solution 
                <a href="https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b">Get 14-Day Plan</a>
            </li>
        </ul>
        
        <p>To your health,<br>WelFore Health Team</p>
    </body>
    </html>
    """

def get_upsell_email(user_name: str = 'there') -> str:
    return f"""
    <html>
    <body>
        <h2>Welcome Back to WelFore Health!</h2>
        <p>Hi {user_name},</p>
        <p>We see you've already received your FREE 3-day meal plan. Ready to take your nutrition to the next level?</p>
        
        <h3>Exclusive Upgrade Options:</h3>
        <ul>
            <li><strong>7-Day Meal Plan</strong> - $19.99
                <a href="https://buy.stripe.com/5kQ7sMddybXy8dsfUR7Vm0a" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Get 7-Day Plan</a>
            </li>
            <li><strong>14-Day Meal Plan</strong> - $29.99
                <a href="https://buy.stripe.com/14A28s7Te3r251gcIF7Vm0b" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Get 14-Day Plan</a>
            </li>
        </ul>
        
        <p>These premium plans include:</p>
        <ul>
            <li>More meal variety</li>
            <li>Detailed nutritional information</li>
            <li>Shopping lists</li>
            <li>Meal prep tips</li>
        </ul>
        
        <p>To your health,<br>WelFore Health Team</p>
    </body>
    </html>
    """
