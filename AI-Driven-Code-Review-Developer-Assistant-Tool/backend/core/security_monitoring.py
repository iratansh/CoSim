import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum
import smtplib
from email.mime.text import MIMEText as MimeText
from email.mime.multipart import MIMEMultipart as MimeMultipart
import redis
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import uuid

from core.config import get_settings

settings = get_settings()

class SecurityEventType(Enum):
    """Security event types for monitoring."""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_REQUEST = "suspicious_request"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PAYMENT_FRAUD = "payment_fraud"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ACCOUNT_LOCKOUT = "account_lockout"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    TWO_FA_ENABLED = "two_fa_enabled"
    TWO_FA_DISABLED = "two_fa_disabled"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"

class SeverityLevel(Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data structure."""
    id: str
    timestamp: datetime
    event_type: SecurityEventType
    severity: SeverityLevel
    user_id: Optional[int]
    ip_address: str
    user_agent: str
    endpoint: str
    details: Dict[str, Any]
    risk_score: int  # 0-100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'endpoint': self.endpoint,
            'details': self.details,
            'risk_score': self.risk_score
        }

class SecurityLogger:
    """Enhanced security logging with structured output."""

    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)

        # Create security-specific log handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event: SecurityEvent):
        """Log security event with structured data."""
        log_data = event.to_dict()

        # Determine log level based on severity
        if event.severity == SeverityLevel.CRITICAL:
            self.logger.critical(json.dumps(log_data))
        elif event.severity == SeverityLevel.HIGH:
            self.logger.error(json.dumps(log_data))
        elif event.severity == SeverityLevel.MEDIUM:
            self.logger.warning(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

        # Store in database for analysis (implement based on your DB)
        self._store_event_in_db(event)

    def _store_event_in_db(self, event: SecurityEvent):
        """Store security event in database for analysis."""
        # Implement database storage here
        pass

class ThreatDetection:
    """Real-time threat detection system."""

    def __init__(self):
        self.failed_logins = defaultdict(deque)
        self.suspicious_ips = defaultdict(int)
        self.rate_limit_violations = defaultdict(deque)
        self.threat_patterns = self._load_threat_patterns()

    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load known threat patterns."""
        return {
            'sql_injection': [
                r'union\s+select',
                r'drop\s+table',
                r'delete\s+from',
                r'\'\s*or\s*\d+=\d+',
                r'exec\s*\(',
                r'script\s*:',
            ],
            'xss': [
                r'<script[^>]*>',
                r'javascript\s*:',
                r'on\w+\s*=',
                r'expression\s*\(',
                r'vbscript\s*:',
            ],
            'path_traversal': [
                r'\.\./|\.\.\%2f',
                r'%2e%2e%2f',
                r'\.\.\\',
            ],
            'command_injection': [
                r';\s*cat\s+',
                r';\s*ls\s+',
                r';\s*id\s*;',
                r'`[^`]*`',
                r'\$\([^)]*\)',
            ]
        }

    def detect_brute_force(self, ip_address: str, user_id: Optional[int] = None) -> bool:
        """Detect brute force attacks."""
        now = datetime.now(timezone.utc)
        window = now.replace(minute=0, second=0, microsecond=0)

        # Track failed logins per IP
        self.failed_logins[ip_address].append(now)

        # Keep only recent attempts (last hour)
        while (self.failed_logins[ip_address] and
               self.failed_logins[ip_address][0] < window):
            self.failed_logins[ip_address].popleft()

        # Detect brute force (>10 attempts in 1 hour)
        return len(self.failed_logins[ip_address]) > 10

    def detect_suspicious_patterns(self, request_data: str) -> List[str]:
        """Detect suspicious patterns in request data."""
        import re
        detected_patterns = []

        for pattern_type, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, request_data, re.IGNORECASE):
                    detected_patterns.append(pattern_type)
                    break

        return detected_patterns

    def calculate_risk_score(self, event_details: Dict[str, Any]) -> int:
        """Calculate risk score (0-100) for security event."""
        score = 0

        # Base scores by event type
        risk_scores = {
            SecurityEventType.LOGIN_FAILURE: 10,
            SecurityEventType.BRUTE_FORCE_ATTACK: 80,
            SecurityEventType.SQL_INJECTION_ATTEMPT: 90,
            SecurityEventType.XSS_ATTEMPT: 70,
            SecurityEventType.UNAUTHORIZED_ACCESS: 85,
            SecurityEventType.PAYMENT_FRAUD: 95,
            SecurityEventType.DATA_BREACH_ATTEMPT: 100,
        }

        event_type = event_details.get('event_type')
        if event_type:
            score = risk_scores.get(SecurityEventType(event_type), 20)

        # Increase score based on factors
        if event_details.get('repeated_attempts', 0) > 5:
            score += 20

        if event_details.get('foreign_ip', False):
            score += 15

        if event_details.get('tor_exit_node', False):
            score += 30

        if event_details.get('suspicious_user_agent', False):
            score += 10

        return min(score, 100)

class SecurityAlertSystem:
    """Security alert and notification system."""

    def __init__(self):
        self.alert_thresholds = {
            SeverityLevel.CRITICAL: 0,   # Alert immediately
            SeverityLevel.HIGH: 5,       # Alert after 5 events
            SeverityLevel.MEDIUM: 20,    # Alert after 20 events
            SeverityLevel.LOW: 100,      # Alert after 100 events
        }
        self.notification_cooldown = 300  # 5 minutes between similar alerts

    async def process_alert(self, event: SecurityEvent):
        """Process security alert and determine if notification is needed."""
        should_alert = self._should_send_alert(event)

        if should_alert:
            await self._send_notifications(event)
            self._update_alert_tracking(event)

    def _should_send_alert(self, event: SecurityEvent) -> bool:
        """Determine if alert should be sent."""
        threshold = self.alert_thresholds.get(event.severity, 10)

        if event.severity == SeverityLevel.CRITICAL:
            return True

        # Check if we've exceeded threshold for this event type
        recent_events = self._get_recent_similar_events(event)
        return len(recent_events) >= threshold

    def _get_recent_similar_events(self, event: SecurityEvent) -> List[SecurityEvent]:
        """Get recent similar events (implement based on your storage)."""
        # Implement database query for similar events in last hour
        return []

    async def _send_notifications(self, event: SecurityEvent):
        """Send security notifications via multiple channels."""
        # Email notification
        await self._send_email_alert(event)

        # Slack notification (if configured)
        await self._send_slack_alert(event)

        # SMS notification for critical events
        if event.severity == SeverityLevel.CRITICAL:
            await self._send_sms_alert(event)

    async def _send_email_alert(self, event: SecurityEvent):
        """Send email security alert."""
        try:
            subject = f"[SECURITY ALERT] {event.severity.value.upper()}: {event.event_type.value}"

            body = f"""
            Security Event Detected:

            Event ID: {event.id}
            Time: {event.timestamp}
            Type: {event.event_type.value}
            Severity: {event.severity.value}
            Risk Score: {event.risk_score}/100
            IP Address: {event.ip_address}
            User ID: {event.user_id or 'Anonymous'}
            Endpoint: {event.endpoint}

            Details:
            {json.dumps(event.details, indent=2)}

            Please investigate immediately if this is a high-severity event.
            """

            # In production, configure proper SMTP settings
            # self._send_email(subject, body, settings.security_email_recipients)

        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")

    async def _send_slack_alert(self, event: SecurityEvent):
        """Send Slack security alert."""
        # Implement Slack webhook integration
        pass

    async def _send_sms_alert(self, event: SecurityEvent):
        """Send SMS for critical security events."""
        # Implement SMS service integration (Twilio, etc.)
        pass

    def _update_alert_tracking(self, event: SecurityEvent):
        """Update alert tracking to prevent spam."""
        # Implement alert tracking in Redis or database
        pass

class SecurityMetrics:
    """Security metrics collection and analysis."""

    def __init__(self):
        self.metrics = defaultdict(int)
        self.hourly_metrics = defaultdict(lambda: defaultdict(int))

    def record_metric(self, metric_name: str, value: int = 1):
        """Record security metric."""
        self.metrics[metric_name] += value

        # Record hourly metrics
        hour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        self.hourly_metrics[hour][metric_name] += value

    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard."""
        return {
            'total_events': sum(self.metrics.values()),
            'events_by_type': dict(self.metrics),
            'hourly_trends': dict(self.hourly_metrics),
            'top_threat_ips': self._get_top_threat_ips(),
            'security_score': self._calculate_overall_security_score(),
        }

    def _get_top_threat_ips(self) -> List[Dict[str, Any]]:
        """Get top threatening IP addresses."""
        # Implement based on your threat tracking
        return []

    def _calculate_overall_security_score(self) -> int:
        """Calculate overall security health score."""
        # Implement security scoring algorithm
        base_score = 85

        # Reduce score based on recent threats
        critical_events = self.metrics.get('critical_events', 0)
        high_events = self.metrics.get('high_events', 0)

        score = base_score - (critical_events * 10) - (high_events * 5)
        return max(score, 0)

class SecurityMonitor:
    """Main security monitoring coordinator."""

    def __init__(self):
        self.logger = SecurityLogger()
        self.threat_detector = ThreatDetection()
        self.alert_system = SecurityAlertSystem()
        self.metrics = SecurityMetrics()
        self.enabled = True

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SeverityLevel,
        user_id: Optional[int] = None,
        ip_address: str = "unknown",
        user_agent: str = "unknown",
        endpoint: str = "unknown",
        details: Dict[str, Any] = None
    ):
        """Log and process security event."""
        if not self.enabled:
            return

        # Create security event
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            details=details or {},
            risk_score=self.threat_detector.calculate_risk_score(details or {})
        )

        # Log the event
        self.logger.log_event(event)

        # Update metrics
        self.metrics.record_metric(f"{event_type.value}_events")
        self.metrics.record_metric(f"{severity.value}_events")

        # Process alerts
        await self.alert_system.process_alert(event)

        # Additional threat detection
        if event_type == SecurityEventType.LOGIN_FAILURE:
            if self.threat_detector.detect_brute_force(ip_address, user_id):
                await self.log_security_event(
                    SecurityEventType.BRUTE_FORCE_ATTACK,
                    SeverityLevel.HIGH,
                    user_id=user_id,
                    ip_address=ip_address,
                    details={'attack_type': 'brute_force_login'}
                )

    def analyze_request_security(self, request_data: str, ip_address: str) -> List[str]:
        """Analyze request for security threats."""
        threats = self.threat_detector.detect_suspicious_patterns(request_data)

        for threat in threats:
            asyncio.create_task(
                self.log_security_event(
                    SecurityEventType.SUSPICIOUS_REQUEST,
                    SeverityLevel.MEDIUM,
                    ip_address=ip_address,
                    details={'threat_type': threat, 'request_data': request_data[:500]}
                )
            )

        return threats

# Global security monitor instance
security_monitor = SecurityMonitor()

# Convenience functions
async def log_login_attempt(user_id: int, ip_address: str, success: bool, details: Dict[str, Any] = None):
    """Log login attempt."""
    event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILURE
    severity = SeverityLevel.LOW if success else SeverityLevel.MEDIUM

    await security_monitor.log_security_event(
        event_type, severity, user_id=user_id, ip_address=ip_address, details=details
    )

async def log_payment_event(event_type: str, user_id: int, amount: int, success: bool, details: Dict[str, Any] = None):
    """Log payment-related security event."""
    if not success and amount > 10000:  # Large failed payment
        await security_monitor.log_security_event(
            SecurityEventType.PAYMENT_FRAUD,
            SeverityLevel.HIGH,
            user_id=user_id,
            details={'amount': amount, 'event_type': event_type, **(details or {})}
        )

async def log_api_access(endpoint: str, user_id: Optional[int], ip_address: str, authorized: bool):
    """Log API access attempt."""
    if not authorized:
        await security_monitor.log_security_event(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            SeverityLevel.MEDIUM,
            user_id=user_id,
            ip_address=ip_address,
            endpoint=endpoint
        )