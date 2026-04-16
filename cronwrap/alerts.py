"""Alerting module for cronwrap — sends notifications on job failure."""

import smtplib
import logging
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = False
    subject_prefix: str = "[cronwrap]"


def send_email_alert(
    config: AlertConfig,
    job_name: str,
    message: str,
    exit_code: Optional[int] = None,
) -> bool:
    """Send an email alert. Returns True on success, False on failure."""
    if not config.email_to or not config.email_from:
        logger.warning("Email alert skipped: email_to or email_from not configured.")
        return False

    subject = f"{config.subject_prefix} Job failed: {job_name}"
    body_lines = [f"Job '{job_name}' failed."]
    if exit_code is not None:
        body_lines.append(f"Exit code: {exit_code}")
    body_lines.append("")
    body_lines.append(message)

    msg = MIMEMultipart()
    msg["From"] = config.email_from
    msg["To"] = config.email_to
    msg["Subject"] = subject
    msg.attach(MIMEText("\n".join(body_lines), "plain"))

    try:
        if config.use_tls:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port)

        if config.smtp_user and config.smtp_password:
            server.login(config.smtp_user, config.smtp_password)

        server.sendmail(config.email_from, config.email_to, msg.as_string())
        server.quit()
        logger.info("Alert email sent to %s", config.email_to)
        return True
    except Exception as exc:
        logger.error("Failed to send alert email: %s", exc)
        return False


def maybe_alert(config: AlertConfig, job_name: str, message: str, exit_code: Optional[int] = None) -> None:
    """Trigger alert if config has a destination set."""
    if config.email_to:
        send_email_alert(config, job_name, message, exit_code)
