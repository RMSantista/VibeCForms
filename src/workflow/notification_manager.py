"""
NotificationManager - Sistema de notificações para workflow events

Responsabilidades:
- Enviar notificações por email quando eventos de workflow ocorrem
- Processar templates de email com substituição de variáveis
- Gerenciar fila de notificações (assíncrono)
- Retry logic para notificações falhadas
- Logging de notificações enviadas
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from string import Template
import queue
import threading


logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manager for sending notifications based on workflow events

    Supports multiple notification channels (email, webhook) and
    handles template rendering, queueing, and retry logic.
    """

    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """
        Initialize NotificationManager

        Args:
            smtp_config: SMTP configuration dict with keys:
                - host: SMTP server host
                - port: SMTP server port
                - username: SMTP username
                - password: SMTP password
                - from_email: Sender email address
                - use_tls: Whether to use TLS (default: True)
        """
        self.smtp_config = smtp_config or self._load_smtp_config_from_env()
        self.notification_queue = queue.Queue()
        self.templates = {}
        self.sent_notifications = []

        # Start background worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

        logger.info("NotificationManager initialized")

    def _load_smtp_config_from_env(self) -> Dict[str, Any]:
        """
        Load SMTP configuration from environment variables

        Returns:
            SMTP config dict
        """
        return {
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("SMTP_FROM_EMAIL", "noreply@vibecforms.com"),
            "use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        }

    def register_template(self, template_name: str, subject: str, body: str):
        """
        Register an email template

        Args:
            template_name: Unique template identifier
            subject: Email subject template (supports $variable substitution)
            body: Email body template (supports $variable substitution)
        """
        self.templates[template_name] = {
            "subject": Template(subject),
            "body": Template(body),
        }
        logger.debug(f"Registered email template: {template_name}")

    def notify(
        self,
        event_type: str,
        process: Dict[str, Any],
        kanban: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send notification for a workflow event

        Args:
            event_type: Type of event (process_created, state_changed, sla_warning, sla_exceeded)
            process: Process dict
            kanban: Kanban definition dict
            additional_data: Additional context data for templates

        Returns:
            True if notification was queued successfully
        """
        # Check if notifications are enabled for this kanban
        notifications_config = kanban.get("notifications", {})
        if not notifications_config.get("enabled", False):
            logger.debug(f"Notifications disabled for kanban '{kanban['id']}'")
            return False

        # Check if this event type is enabled
        events_config = notifications_config.get("events", {})
        if not events_config.get(event_type, False):
            logger.debug(
                f"Event type '{event_type}' disabled for kanban '{kanban['id']}'"
            )
            return False

        # Get notification channels
        channels = notifications_config.get("channels", [])

        # Send email if configured
        if "email" in channels:
            email_config = notifications_config.get("email_config", {})
            recipients = email_config.get("recipients", [])
            template_name = email_config.get("template", "default")

            if recipients:
                self._queue_email_notification(
                    recipients=recipients,
                    template_name=template_name,
                    event_type=event_type,
                    process=process,
                    kanban=kanban,
                    additional_data=additional_data,
                )

        return True

    def _queue_email_notification(
        self,
        recipients: List[str],
        template_name: str,
        event_type: str,
        process: Dict[str, Any],
        kanban: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Queue an email notification for background sending

        Args:
            recipients: List of recipient email addresses
            template_name: Template to use
            event_type: Event type
            process: Process dict
            kanban: Kanban dict
            additional_data: Additional template context
        """
        notification = {
            "type": "email",
            "recipients": recipients,
            "template_name": template_name,
            "event_type": event_type,
            "process": process,
            "kanban": kanban,
            "additional_data": additional_data or {},
            "queued_at": datetime.now().isoformat(),
            "retry_count": 0,
        }

        self.notification_queue.put(notification)
        logger.debug(f"Queued email notification for {len(recipients)} recipients")

    def _process_queue(self):
        """
        Background worker thread that processes notification queue
        """
        while True:
            try:
                notification = self.notification_queue.get(timeout=1)

                if notification["type"] == "email":
                    success = self._send_email_notification(notification)

                    if success:
                        self.sent_notifications.append(
                            {
                                **notification,
                                "sent_at": datetime.now().isoformat(),
                                "status": "sent",
                            }
                        )
                    else:
                        # Retry logic
                        if notification["retry_count"] < 3:
                            notification["retry_count"] += 1
                            self.notification_queue.put(notification)
                            logger.warning(
                                f"Retrying notification (attempt {notification['retry_count']})"
                            )
                        else:
                            self.sent_notifications.append(
                                {
                                    **notification,
                                    "sent_at": datetime.now().isoformat(),
                                    "status": "failed",
                                }
                            )
                            logger.error("Max retries reached, notification failed")

                self.notification_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing notification queue: {e}")

    def _send_email_notification(self, notification: Dict[str, Any]) -> bool:
        """
        Send an email notification

        Args:
            notification: Notification dict

        Returns:
            True if email sent successfully
        """
        try:
            # Get template
            template_name = notification["template_name"]
            if template_name not in self.templates:
                # Use default template
                template_name = "default"
                if template_name not in self.templates:
                    # Register default template if not exists
                    self._register_default_templates()

            template = self.templates.get(template_name, self.templates["default"])

            # Prepare template context
            context = self._prepare_template_context(
                notification["event_type"],
                notification["process"],
                notification["kanban"],
                notification["additional_data"],
            )

            # Render template
            subject = template["subject"].safe_substitute(context)
            body = template["body"].safe_substitute(context)

            # Send email
            return self._send_smtp_email(
                recipients=notification["recipients"], subject=subject, body=body
            )

        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False

    def _prepare_template_context(
        self,
        event_type: str,
        process: Dict[str, Any],
        kanban: Dict[str, Any],
        additional_data: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Prepare template substitution context

        Args:
            event_type: Event type
            process: Process dict
            kanban: Kanban dict
            additional_data: Additional context

        Returns:
            Dict with template variables
        """
        context = {
            "event_type": event_type,
            "process_id": process.get("process_id", ""),
            "kanban_name": kanban.get("name", ""),
            "kanban_id": kanban.get("id", ""),
            "current_state": process.get("current_state", ""),
            "created_at": process.get("created_at", ""),
            "updated_at": process.get("updated_at", ""),
            **additional_data,
        }

        # Add field values with safe keys
        field_values = process.get("field_values", {})
        for key, value in field_values.items():
            safe_key = key.replace(" ", "_").replace("-", "_")
            context[f"field_{safe_key}"] = str(value)

        return context

    def _send_smtp_email(self, recipients: List[str], subject: str, body: str) -> bool:
        """
        Send email via SMTP

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML or plain text)

        Returns:
            True if email sent successfully
        """
        if not self.smtp_config.get("username") or not self.smtp_config.get("password"):
            logger.warning("SMTP credentials not configured, skipping email send")
            return False

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_config["from_email"]
            msg["To"] = ", ".join(recipients)

            # Attach body (assuming HTML)
            html_part = MIMEText(body, "html")
            msg.attach(html_part)

            # Connect to SMTP server
            smtp_class = smtplib.SMTP
            server = smtp_class(self.smtp_config["host"], self.smtp_config["port"])

            if self.smtp_config.get("use_tls", True):
                server.starttls()

            server.login(self.smtp_config["username"], self.smtp_config["password"])

            # Send email
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return False

    def _register_default_templates(self):
        """Register default email templates"""

        # Default template
        self.register_template(
            "default",
            subject="[Workflow] $event_type - $kanban_name",
            body="""
                <html>
                <head><style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                    .content { background: white; padding: 20px; border: 1px solid #ddd; border-top: none; }
                    .footer { background: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; }
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>Notificação de Workflow</h2>
                        </div>
                        <div class="content">
                            <div class="info-row">
                                <span class="label">Evento:</span> $event_type
                            </div>
                            <div class="info-row">
                                <span class="label">Kanban:</span> $kanban_name
                            </div>
                            <div class="info-row">
                                <span class="label">Processo:</span> $process_id
                            </div>
                            <div class="info-row">
                                <span class="label">Estado Atual:</span> $current_state
                            </div>
                            <div class="info-row">
                                <span class="label">Última Atualização:</span> $updated_at
                            </div>
                        </div>
                        <div class="footer">
                            <p>Esta é uma notificação automática do sistema VibeCForms Workflow.</p>
                        </div>
                    </div>
                </body>
                </html>
            """,
        )

        # Process created template
        self.register_template(
            "process_created",
            subject="[Workflow] Novo processo criado - $kanban_name",
            body="""
                <html>
                <head><style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #28a745; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                    .content { background: white; padding: 20px; border: 1px solid #ddd; border-top: none; }
                    .footer { background: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; }
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>✅ Novo Processo Criado</h2>
                        </div>
                        <div class="content">
                            <p>Um novo processo foi criado no workflow <strong>$kanban_name</strong>.</p>
                            <div class="info-row">
                                <span class="label">Processo ID:</span> $process_id
                            </div>
                            <div class="info-row">
                                <span class="label">Estado Inicial:</span> $current_state
                            </div>
                            <div class="info-row">
                                <span class="label">Criado em:</span> $created_at
                            </div>
                        </div>
                        <div class="footer">
                            <p>Esta é uma notificação automática do sistema VibeCForms Workflow.</p>
                        </div>
                    </div>
                </body>
                </html>
            """,
        )

        # State changed template
        self.register_template(
            "state_changed",
            subject="[Workflow] Mudança de estado - $kanban_name",
            body="""
                <html>
                <head><style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #007bff; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                    .content { background: white; padding: 20px; border: 1px solid #ddd; border-top: none; }
                    .footer { background: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; }
                    .transition { background: #e3f2fd; padding: 10px; border-radius: 4px; margin: 15px 0; }
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🔄 Mudança de Estado</h2>
                        </div>
                        <div class="content">
                            <p>O processo avançou no workflow <strong>$kanban_name</strong>.</p>
                            <div class="info-row">
                                <span class="label">Processo ID:</span> $process_id
                            </div>
                            <div class="transition">
                                <strong>$previous_state</strong> → <strong>$current_state</strong>
                            </div>
                            <div class="info-row">
                                <span class="label">Atualizado em:</span> $updated_at
                            </div>
                        </div>
                        <div class="footer">
                            <p>Esta é uma notificação automática do sistema VibeCForms Workflow.</p>
                        </div>
                    </div>
                </body>
                </html>
            """,
        )

        # SLA warning template
        self.register_template(
            "sla_warning",
            subject="[Workflow] ⚠️ Alerta de SLA - $kanban_name",
            body="""
                <html>
                <head><style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #ffc107; color: #000; padding: 20px; border-radius: 8px 8px 0 0; }
                    .content { background: white; padding: 20px; border: 1px solid #ddd; border-top: none; }
                    .footer { background: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; }
                    .warning-box { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>⚠️ Alerta de SLA</h2>
                        </div>
                        <div class="content">
                            <div class="warning-box">
                                <p><strong>Atenção!</strong> O processo está próximo de exceder o SLA.</p>
                            </div>
                            <div class="info-row">
                                <span class="label">Processo ID:</span> $process_id
                            </div>
                            <div class="info-row">
                                <span class="label">Kanban:</span> $kanban_name
                            </div>
                            <div class="info-row">
                                <span class="label">Estado Atual:</span> $current_state
                            </div>
                            <div class="info-row">
                                <span class="label">Tempo Restante:</span> $sla_remaining
                            </div>
                        </div>
                        <div class="footer">
                            <p>Esta é uma notificação automática do sistema VibeCForms Workflow.</p>
                        </div>
                    </div>
                </body>
                </html>
            """,
        )

        # SLA exceeded template
        self.register_template(
            "sla_exceeded",
            subject="[Workflow] 🚨 SLA Excedido - $kanban_name",
            body="""
                <html>
                <head><style>
                    body { font-family: Arial, sans-serif; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #dc3545; color: white; padding: 20px; border-radius: 8px 8px 0 0; }
                    .content { background: white; padding: 20px; border: 1px solid #ddd; border-top: none; }
                    .footer { background: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #666; }
                    .info-row { margin: 10px 0; }
                    .label { font-weight: bold; }
                    .error-box { background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 15px 0; }
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🚨 SLA Excedido</h2>
                        </div>
                        <div class="content">
                            <div class="error-box">
                                <p><strong>Urgente!</strong> O processo excedeu o SLA estabelecido.</p>
                            </div>
                            <div class="info-row">
                                <span class="label">Processo ID:</span> $process_id
                            </div>
                            <div class="info-row">
                                <span class="label">Kanban:</span> $kanban_name
                            </div>
                            <div class="info-row">
                                <span class="label">Estado Atual:</span> $current_state
                            </div>
                            <div class="info-row">
                                <span class="label">Tempo Excedido:</span> $sla_exceeded_by
                            </div>
                        </div>
                        <div class="footer">
                            <p>Esta é uma notificação automática do sistema VibeCForms Workflow.</p>
                        </div>
                    </div>
                </body>
                </html>
            """,
        )

    def get_notification_history(
        self, limit: int = 50, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notification history

        Args:
            limit: Maximum number of notifications to return
            status: Filter by status ('sent', 'failed', or None for all)

        Returns:
            List of notification dicts
        """
        notifications = self.sent_notifications

        if status:
            notifications = [n for n in notifications if n.get("status") == status]

        return notifications[-limit:]

    def get_queue_size(self) -> int:
        """
        Get current notification queue size

        Returns:
            Number of pending notifications
        """
        return self.notification_queue.qsize()
