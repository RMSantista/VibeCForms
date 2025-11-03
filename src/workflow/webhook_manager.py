"""
WebhookManager - Sistema de webhooks para workflow events

Responsabilidades:
- Enviar requisições HTTP POST para webhooks configurados
- Processar configurações de headers com substituição de variáveis
- Gerenciar fila de webhooks (assíncrono)
- Retry logic para webhooks falhados
- Timeout handling
- Logging de chamadas de webhook
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import queue
import threading
from string import Template


logger = logging.getLogger(__name__)


class WebhookManager:
    """
    Manager for sending webhooks based on workflow events

    Handles HTTP POST requests to configured endpoints with
    automatic retries, queueing, and environment variable substitution.
    """

    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize WebhookManager

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.webhook_queue = queue.Queue()
        self.sent_webhooks = []

        # Start background worker thread
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

        logger.info("WebhookManager initialized")

    def notify(
        self,
        event_type: str,
        process: Dict[str, Any],
        kanban: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send webhook notification for a workflow event

        Args:
            event_type: Type of event (process_created, state_changed, etc.)
            process: Process dict
            kanban: Kanban definition dict
            additional_data: Additional context data

        Returns:
            True if webhook was queued successfully
        """
        # Check if webhooks are enabled for this kanban
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

        # Send webhook if configured
        if "webhook" in channels:
            webhook_config = notifications_config.get("webhook_config", {})
            url = webhook_config.get("url")

            if url:
                self._queue_webhook(
                    url=url,
                    headers=webhook_config.get("headers", {}),
                    event_type=event_type,
                    process=process,
                    kanban=kanban,
                    additional_data=additional_data,
                )

        return True

    def _queue_webhook(
        self,
        url: str,
        headers: Dict[str, str],
        event_type: str,
        process: Dict[str, Any],
        kanban: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Queue a webhook for background sending

        Args:
            url: Webhook URL
            headers: HTTP headers (support ${VAR} substitution)
            event_type: Event type
            process: Process dict
            kanban: Kanban dict
            additional_data: Additional payload data
        """
        webhook = {
            "url": url,
            "headers": self._substitute_env_vars(headers),
            "event_type": event_type,
            "process": process,
            "kanban": kanban,
            "additional_data": additional_data or {},
            "queued_at": datetime.now().isoformat(),
            "retry_count": 0,
        }

        self.webhook_queue.put(webhook)
        logger.debug(f"Queued webhook to {url}")

    def _process_queue(self):
        """
        Background worker thread that processes webhook queue
        """
        while True:
            try:
                webhook = self.webhook_queue.get(timeout=1)

                success, response_data = self._send_webhook(webhook)

                if success:
                    self.sent_webhooks.append(
                        {
                            **webhook,
                            "sent_at": datetime.now().isoformat(),
                            "status": "sent",
                            "response": response_data,
                        }
                    )
                else:
                    # Retry logic
                    if webhook["retry_count"] < self.max_retries:
                        webhook["retry_count"] += 1
                        self.webhook_queue.put(webhook)
                        logger.warning(
                            f"Retrying webhook (attempt {webhook['retry_count']})"
                        )
                    else:
                        self.sent_webhooks.append(
                            {
                                **webhook,
                                "sent_at": datetime.now().isoformat(),
                                "status": "failed",
                                "response": response_data,
                            }
                        )
                        logger.error("Max retries reached, webhook failed")

                self.webhook_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing webhook queue: {e}")

    def _send_webhook(
        self, webhook: Dict[str, Any]
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Send webhook via HTTP POST

        Args:
            webhook: Webhook dict

        Returns:
            Tuple of (success, response_data)
        """
        try:
            # Prepare payload
            payload = self._prepare_payload(
                webhook["event_type"],
                webhook["process"],
                webhook["kanban"],
                webhook["additional_data"],
            )

            # Send POST request
            response = requests.post(
                webhook["url"],
                json=payload,
                headers=webhook["headers"],
                timeout=self.timeout,
            )

            # Check response status
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(
                    f"Webhook sent successfully to {webhook['url']} (status: {response.status_code})"
                )
                return True, {
                    "status_code": response.status_code,
                    "body": response.text[:500],  # Limit response body size
                }
            else:
                logger.warning(
                    f"Webhook failed with status {response.status_code}: {response.text[:200]}"
                )
                return False, {
                    "status_code": response.status_code,
                    "body": response.text[:500],
                }

        except requests.exceptions.Timeout:
            logger.error(f"Webhook timeout to {webhook['url']}")
            return False, {"error": "timeout"}
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Webhook connection error to {webhook['url']}: {e}")
            return False, {"error": f"connection_error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error sending webhook to {webhook['url']}: {e}")
            return False, {"error": str(e)}

    def _prepare_payload(
        self,
        event_type: str,
        process: Dict[str, Any],
        kanban: Dict[str, Any],
        additional_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Prepare webhook payload

        Args:
            event_type: Event type
            process: Process dict
            kanban: Kanban dict
            additional_data: Additional context

        Returns:
            Payload dict
        """
        return {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "kanban": {"id": kanban.get("id"), "name": kanban.get("name")},
            "process": {
                "process_id": process.get("process_id"),
                "current_state": process.get("current_state"),
                "created_at": process.get("created_at"),
                "updated_at": process.get("updated_at"),
                "field_values": process.get("field_values", {}),
                "tags": process.get("tags", []),
                "assigned_to": process.get("assigned_to"),
                "sla": process.get("sla"),
            },
            **additional_data,
        }

    def _substitute_env_vars(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Substitute environment variables in headers

        Supports ${VAR_NAME} syntax

        Args:
            headers: Original headers dict

        Returns:
            Headers with substituted values
        """
        substituted = {}

        for key, value in headers.items():
            if isinstance(value, str) and "${" in value:
                # Use Template for safe substitution
                template = Template(value)
                try:
                    substituted[key] = template.substitute(os.environ)
                except KeyError as e:
                    logger.warning(f"Environment variable not found: {e}")
                    substituted[key] = value
            else:
                substituted[key] = value

        return substituted

    def send_webhook_now(
        self,
        url: str,
        payload: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Send webhook immediately (synchronous, no queuing)

        Args:
            url: Webhook URL
            payload: Payload dict
            headers: Optional HTTP headers

        Returns:
            Tuple of (success, response_data)
        """
        headers = self._substitute_env_vars(headers or {})

        webhook = {
            "url": url,
            "headers": headers,
            "event_type": "manual",
            "process": {},
            "kanban": {},
            "additional_data": payload,
            "queued_at": datetime.now().isoformat(),
            "retry_count": 0,
        }

        # Override payload preparation
        webhook["_payload"] = payload

        return self._send_webhook_direct(url, payload, headers)

    def _send_webhook_direct(
        self, url: str, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Send webhook directly without queue

        Args:
            url: Webhook URL
            payload: Payload dict
            headers: HTTP headers

        Returns:
            Tuple of (success, response_data)
        """
        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout
            )

            if response.status_code >= 200 and response.status_code < 300:
                return True, {
                    "status_code": response.status_code,
                    "body": response.text[:500],
                }
            else:
                return False, {
                    "status_code": response.status_code,
                    "body": response.text[:500],
                }

        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False, {"error": str(e)}

    def get_webhook_history(
        self, limit: int = 50, status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get webhook history

        Args:
            limit: Maximum number of webhooks to return
            status: Filter by status ('sent', 'failed', or None for all)

        Returns:
            List of webhook dicts
        """
        webhooks = self.sent_webhooks

        if status:
            webhooks = [w for w in webhooks if w.get("status") == status]

        return webhooks[-limit:]

    def get_queue_size(self) -> int:
        """
        Get current webhook queue size

        Returns:
            Number of pending webhooks
        """
        return self.webhook_queue.qsize()

    def test_webhook(
        self, url: str, headers: Optional[Dict[str, str]] = None
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Test webhook connectivity with ping payload

        Args:
            url: Webhook URL to test
            headers: Optional HTTP headers

        Returns:
            Tuple of (success, response_data)
        """
        payload = {
            "event_type": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "Webhook test from VibeCForms Workflow",
        }

        return self.send_webhook_now(url, payload, headers)
