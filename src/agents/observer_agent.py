"""
Observer Agent (주방장/Chef) - Background monitoring agent.
Handles log collection, error analysis, and alerting.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import redis.asyncio as aioredis
import sentry_sdk
import structlog

from src.config.settings import settings
from src.models.events import AgentEvent, EventType

logger = logging.getLogger(__name__)


class ObserverAgent:
    """
    Observer Agent for monitoring and analysis.
    Runs in background, processing events from the Business Agent.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        sentry_dsn: str | None = None,
        logtail_token: str | None = None,
    ):
        """
        Initialize the Observer Agent.

        Args:
            redis_url: Redis connection URL
            sentry_dsn: Sentry DSN for error tracking
            logtail_token: Better Stack (Logtail) token
        """
        self.redis_url = redis_url or settings.redis_url
        self.sentry_dsn = sentry_dsn
        self.logtail_token = logtail_token

        self.event_queue = "agent:events"
        self.redis: aioredis.Redis | None = None

        # Initialize structured logging
        self.logger = structlog.get_logger()

        # Analysis state
        self.error_counts: dict[str, int] = {}
        self.latency_buffer: list[float] = []
        self.api_call_counts: dict[str, int] = {}

        # Control flags
        self.running = False

    async def initialize(self):
        """Initialize connections and integrations."""
        # Connect to Redis
        self.redis = aioredis.from_url(self.redis_url)
        await self.redis.ping()
        self.logger.info("Connected to Redis", url=self.redis_url)

        # Initialize Sentry
        if self.sentry_dsn:
            sentry_sdk.init(
                dsn=self.sentry_dsn,
                environment=settings.sentry_environment,
            )
            self.logger.info("Sentry initialized")

        # Initialize Better Stack (Logtail)
        if self.logtail_token:
            try:
                from logtail import LogtailHandler

                handler = LogtailHandler(source_token=self.logtail_token)
                logging.getLogger().addHandler(handler)
                self.logger.info("Better Stack (Logtail) initialized")
            except ImportError:
                self.logger.warning("logtail-python not installed, skipping Better Stack")

    async def run(self):
        """Main event processing loop."""
        await self.initialize()

        self.running = True
        self.logger.info("Observer Agent started", agent_type="observer")

        while self.running:
            try:
                # Block and wait for events from queue
                event_data = await self.redis.blpop(self.event_queue, timeout=1)

                if event_data:
                    # event_data is (queue_name, data)
                    _, raw_data = event_data
                    event = AgentEvent.model_validate_json(raw_data)
                    await self.process_event(event)

            except asyncio.CancelledError:
                self.logger.info("Observer Agent cancelled")
                break
            except Exception as e:
                self.logger.error("Event processing failed", error=str(e))
                if self.sentry_dsn:
                    sentry_sdk.capture_exception(e)

    async def shutdown(self):
        """Graceful shutdown."""
        self.running = False

        if self.redis:
            await self.redis.close()

        self.logger.info("Observer Agent shutdown complete")

    async def process_event(self, event: AgentEvent):
        """
        Process a single event from the queue.

        Args:
            event: The agent event to process
        """
        # 1. Log the event
        self.log_event(event)

        # 2. Handle errors
        if event.event_type == EventType.ERROR_OCCURRED:
            await self.handle_error(event)

        # 3. Collect metrics
        if event.latency_ms:
            self.latency_buffer.append(event.latency_ms)

        # 4. Track API calls
        if event.event_type == EventType.NAVER_API_CALLED:
            api_type = event.payload.get("api_type", "unknown")
            self.api_call_counts[api_type] = self.api_call_counts.get(api_type, 0) + 1

        # 5. Detect anomalies
        if settings.anomaly_detection_enabled:
            await self.detect_anomalies(event)

        # 6. Periodic analysis (every 100 events)
        if len(self.latency_buffer) >= 100:
            await self.analyze_and_report()

    def log_event(self, event: AgentEvent):
        """Log event to Better Stack."""
        log_data = {
            "event": event.event_type.value,
            "thread_id": event.thread_id,
            "user_id": event.user_id,
            "latency_ms": event.latency_ms,
            "token_count": event.token_count,
            **event.payload,
        }

        if event.error_code:
            self.logger.error(
                event.error_message or "Error occurred",
                **log_data,
                error_code=event.error_code,
            )
        else:
            self.logger.info(f"Event: {event.event_type.value}", **log_data)

    async def handle_error(self, event: AgentEvent):
        """Handle error events."""
        error_type = event.error_code or "unknown"
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Send to Sentry
        if self.sentry_dsn:
            with sentry_sdk.push_scope() as scope:
                scope.set_context("event", event.model_dump())
                scope.set_tag("error_type", error_type)
                scope.set_tag("thread_id", event.thread_id)

                sentry_sdk.capture_message(
                    event.error_message or f"Error: {error_type}",
                    level="error",
                )

        # Alert on repeated errors
        if self.error_counts[error_type] >= 5:
            await self.send_alert(
                severity="critical",
                message=f"Repeated errors: {error_type} ({self.error_counts[error_type]} times)",
                context={"thread_id": event.thread_id},
            )

    async def detect_anomalies(self, event: AgentEvent):
        """Detect anomalies in events."""
        # High latency detection
        if event.latency_ms and event.latency_ms > 5000:
            await self.send_alert(
                severity="warning",
                message=f"High latency detected: {event.latency_ms}ms",
                context={"thread_id": event.thread_id, "latency_ms": event.latency_ms},
            )

        # Prompt injection detection
        if event.event_type == EventType.PROMPT_INJECTION_DETECTED:
            await self.send_alert(
                severity="critical",
                message="Prompt injection attempt detected",
                context=event.payload,
            )

        # Rate limiting events
        if event.event_type == EventType.RATE_LIMITED:
            self.logger.warning(
                "Rate limit triggered",
                thread_id=event.thread_id,
                **event.payload,
            )

    async def analyze_and_report(self):
        """Generate periodic analysis report."""
        if not self.latency_buffer:
            return

        # Calculate statistics
        avg_latency = sum(self.latency_buffer) / len(self.latency_buffer)
        sorted_latencies = sorted(self.latency_buffer)
        p50_latency = sorted_latencies[len(sorted_latencies) // 2]
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)]

        report = {
            "period": "last_100_events",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "avg_latency_ms": round(avg_latency, 2),
                "p50_latency_ms": round(p50_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "p99_latency_ms": round(p99_latency, 2),
            },
            "error_counts": dict(self.error_counts),
            "api_call_counts": dict(self.api_call_counts),
            "total_events": len(self.latency_buffer),
        }

        self.logger.info("Performance report", **report)

        # Reset buffers
        self.latency_buffer = []
        self.error_counts = {}
        self.api_call_counts = {}

    async def send_alert(
        self,
        severity: str,
        message: str,
        context: dict[str, Any] | None = None,
    ):
        """Send alert via configured channels."""
        alert_data = {
            "severity": severity,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "context": context or {},
        }

        self.logger.warning("Alert triggered", **alert_data)

        # Send to Slack if configured
        if settings.slack_webhook_url:
            await self._send_slack_alert(alert_data)

    async def _send_slack_alert(self, alert_data: dict[str, Any]):
        """Send alert to Slack webhook."""
        try:
            import httpx

            emoji = {
                "info": ":information_source:",
                "warning": ":warning:",
                "critical": ":rotating_light:",
            }.get(alert_data["severity"], ":bell:")

            payload = {
                "text": f"{emoji} *{alert_data['severity'].upper()}*: {alert_data['message']}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{emoji} *{alert_data['severity'].upper()}*\n{alert_data['message']}",
                        },
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"_Time: {alert_data['timestamp']}_",
                            }
                        ],
                    },
                ],
            }

            async with httpx.AsyncClient() as client:
                await client.post(settings.slack_webhook_url, json=payload, timeout=5.0)

        except Exception as e:
            self.logger.error("Failed to send Slack alert", error=str(e))
