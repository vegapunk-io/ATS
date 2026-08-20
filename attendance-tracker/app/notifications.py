"""Email notification service for attendance alerts and reminders."""
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from .config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Send an HTML email. Returns True on success, False on failure."""
    if not settings.email_enabled:
        logger.info(f"Email disabled. Would send to {to_email}: {subject}")
        return False

    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("SMTP credentials not configured")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_check_in_reminder(email: str, name: str) -> bool:
    """Send a daily check-in reminder."""
    subject = f"⏰ Check-in Reminder - {settings.app_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">{settings.app_name}</h2>
        </div>
        <div style="background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0;">
            <p>Hello <strong>{name}</strong>,</p>
            <p>This is a friendly reminder to check in for today.</p>
            <p style="color: #64748b; font-size: 13px;">Date: {datetime.now().strftime('%A, %B %d, %Y')}</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;">
            <p style="color: #94a3b8; font-size: 12px;">This is an automated message from {settings.app_name}.</p>
        </div>
    </div>
    """
    return send_email(email, subject, html)


def send_late_check_in_alert(
    admin_email: str,
    admin_name: str,
    employee_name: str,
    check_in_time: str,
    shift_start: str,
) -> bool:
    """Send an alert to admin when an employee checks in late."""
    subject = f"⚠️ Late Check-in Alert - {employee_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">⚠️ Late Check-in Alert</h2>
        </div>
        <div style="background: #fef2f2; padding: 20px; border: 1px solid #fecaca;">
            <p>Hello <strong>{admin_name}</strong>,</p>
            <p><strong>{employee_name}</strong> checked in late today.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr>
                    <td style="padding: 8px; color: #64748b;">Shift Start:</td>
                    <td style="padding: 8px; font-weight: bold;">{shift_start}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #64748b;">Actual Check-in:</td>
                    <td style="padding: 8px; font-weight: bold; color: #dc2626;">{check_in_time}</td>
                </tr>
            </table>
            <hr style="border: none; border-top: 1px solid #fecaca; margin: 16px 0;">
            <p style="color: #94a3b8; font-size: 12px;">This is an automated message from {settings.app_name}.</p>
        </div>
    </div>
    """
    return send_email(admin_email, subject, html)


def send_no_show_alert(admin_email: str, admin_name: str, employee_name: str) -> bool:
    """Send an alert when an employee hasn't checked in by end of day."""
    subject = f"🚨 No Show Alert - {employee_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #d97706, #f59e0b); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">🚨 No Show Alert</h2>
        </div>
        <div style="background: #fffbeb; padding: 20px; border: 1px solid #fde68a;">
            <p>Hello <strong>{admin_name}</strong>,</p>
            <p><strong>{employee_name}</strong> has not checked in today.</p>
            <p style="color: #92400e; font-size: 13px;">Please follow up if needed.</p>
            <hr style="border: none; border-top: 1px solid #fde68a; margin: 16px 0;">
            <p style="color: #94a3b8; font-size: 12px;">This is an automated message from {settings.app_name}.</p>
        </div>
    </div>
    """
    return send_email(admin_email, subject, html)


def send_leave_approved(email: str, name: str, leave_type: str, start_date: str, end_date: str) -> bool:
    """Send leave approval notification to employee."""
    subject = f"✅ Leave Approved - {settings.app_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #16a34a, #22c55e); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">✅ Leave Approved</h2>
        </div>
        <div style="background: #f0fdf4; padding: 20px; border: 1px solid #bbf7d0;">
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your <strong>{leave_type}</strong> leave request has been <strong style="color: #16a34a;">approved</strong>.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr><td style="padding: 8px; color: #64748b;">Type:</td><td style="padding: 8px; font-weight: bold;">{leave_type.title()}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">From:</td><td style="padding: 8px; font-weight: bold;">{start_date}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">To:</td><td style="padding: 8px; font-weight: bold;">{end_date}</td></tr>
            </table>
            <hr style="border: none; border-top: 1px solid #bbf7d0; margin: 16px 0;">
            <p style="color: #94a3b8; font-size: 12px;">This is an automated message from {settings.app_name}.</p>
        </div>
    </div>
    """
    return send_email(email, subject, html)


def send_leave_rejected(email: str, name: str, leave_type: str, start_date: str, end_date: str, reason: str | None = None) -> bool:
    """Send leave rejection notification to employee."""
    subject = f"❌ Leave Rejected - {settings.app_name}"
    reason_html = f"<p style='color: #92400e; margin-top: 8px;'><strong>Reason:</strong> {reason}</p>" if reason else ""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #dc2626, #ef4444); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">❌ Leave Rejected</h2>
        </div>
        <div style="background: #fef2f2; padding: 20px; border: 1px solid #fecaca;">
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your <strong>{leave_type}</strong> leave request has been <strong style="color: #dc2626;">rejected</strong>.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr><td style="padding: 8px; color: #64748b;">Type:</td><td style="padding: 8px; font-weight: bold;">{leave_type.title()}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">From:</td><td style="padding: 8px; font-weight: bold;">{start_date}</td></tr>
                <tr><td style="padding: 8px; color: #64748b;">To:</td><td style="padding: 8px; font-weight: bold;">{end_date}</td></tr>
            </table>
            {reason_html}
            <hr style="border: none; border-top: 1px solid #fecaca; margin: 16px 0;">
            <p style="color: #94a3b8; font-size: 12px;">This is an automated message from {settings.app_name}.</p>
        </div>
    </div>
    """
    return send_email(email, subject, html)


def send_overtime_approved(email: str, name: str, date: str, hours: float) -> bool:
    """Send overtime approval notification."""
    subject = f"⏰ Overtime Approved - {settings.app_name}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
            <h2 style="margin: 0;">⏰ Overtime Approved</h2>
        </div>
        <div style="background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0;">
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your overtime request for <strong>{hours}h</strong> on <strong>{date}</strong> has been approved.</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;">
            <p style="color: #94a3b8; font-size: 12px;">This is an automated message from {settings.app_name}.</p>
        </div>
    </div>
    """
    return send_email(email, subject, html)
