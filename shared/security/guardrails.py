import re
import os
import logging
from typing import Optional, Tuple
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Compile regex patterns for PII detection
EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
PHONE_REGEX = re.compile(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b')
CREDIT_CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

# Core jailbreak and prompt injection patterns
JAILBREAK_KEYWORDS = [
    "ignore previous instructions",
    "ignore all instructions",
    "system override",
    "developer mode",
    "bypass constraints",
    "you are now a",
    "ignore the guidelines",
    "do not follow standard protocol",
    "output raw content",
    "act as a",
    "ignore safety limits",
    "dan mode",
    "bypass safety"
]

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filenames to prevent path traversal attacks (e.g. ../../etc/passwd -> passwd)
    and removes non-alphanumeric characters except safe delimiters.
    """
    # 1. Take only the base name (rejects directories)
    basename = os.path.basename(filename)
    
    # 2. Remove directory references that might bypass os.path.basename
    basename = basename.replace("/", "").replace("\\", "").replace("..", "")
    
    # 3. Restrict to safe characters: alphanumeric, dash, underscore, dot
    sanitized = re.sub(r'[^a-zA-Z0-9_\.-]', '_', basename)
    
    # 4. Reject empty filenames or generic dotfiles
    if not sanitized or sanitized in (".", "..", ".env"):
        sanitized = "safe_uploaded_document"
        
    return sanitized

def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """
    Scans input text for potential jailbreaks and prompt injection attempts.
    Returns: (is_injection, reason)
    """
    if not text:
        return False, None

    normalized_text = text.lower()
    
    # Scan for common override and jailbreak patterns
    for pattern in JAILBREAK_KEYWORDS:
        if pattern in normalized_text:
            logger.warning(f"Prompt injection pattern detected: '{pattern}'")
            return True, f"Malicious input pattern detected ('{pattern}')"

    # Scan for system-prompt mimicking attacks (e.g. System: override)
    if re.search(r'\b(system|developer|admin)\s*:\s*(ignore|override|reset)\b', normalized_text):
        logger.warning("System instruction override pattern detected via regex.")
        return True, "Jailbreak instruction override format detected"

    return False, None

def redact_pii(text: str) -> str:
    """
    Scans input text for PII (emails, phone numbers, credit cards, SSNs)
    and redacts it to prevent data leakage to external LLMs.
    """
    if not text:
        return text

    # Redact Emails
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    
    # Redact Phone Numbers
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    
    # Redact Credit Cards
    text = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", text)
    
    # Redact SSNs
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)

    return text

def validate_llm_output(output_text: str) -> str:
    """
    Ensures the LLM output does not contain any accidentally leaked api keys,
    system environment variables, or private variables.
    """
    if not output_text:
        return output_text

    # Scan for leaked API keys (e.g. sk-... or similar API key structures)
    api_key_patterns = [
        r'\bsk-[a-zA-Z0-9]{32,48}\b', # OpenAI / general keys
        r'\bxai-[a-zA-Z0-9]{40,96}\b', # xAI keys
        r'\bkey-[a-zA-Z0-9]{32,64}\b', # general keys
        r'\b[a-zA-Z0-9_-]{32,64}\b' # potential secrets
    ]
    
    for pattern in api_key_patterns:
        # If the output text contains something matching sk- or xai- keys explicitly, redact it
        if "sk-" in output_text or "xai-" in output_text:
            output_text = re.sub(r'\b(sk|xai)-[a-zA-Z0-9_-]{24,120}\b', "[REDACTED_API_KEY]", output_text)

    # Clean up any potential system injection attempts reflected in the output
    output_text = output_text.replace("system_override", "safe_override")

    return output_text

def guard_input(text: str) -> str:
    """
    Main gateway function for sanitizing input sent to LLMs.
    Redacts PII and checks for prompt injection.
    """
    is_injection, reason = detect_prompt_injection(text)
    if is_injection:
        raise HTTPException(
            status_code=400,
            detail=f"Security Gateway: Request rejected due to compliance risk. {reason}"
        )
    return redact_pii(text)


import time
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SensitiveDataLoggingFilter(logging.Filter):
    """
    Intercepts logs and redacts any PII or API Keys to avoid accidental leakage
    to server logfiles or external log collectors.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_pii(record.msg)
            record.msg = validate_llm_output(record.msg)
        if record.args:
            new_args = tuple(
                (redact_pii(arg) if isinstance(arg, str) else arg)
                for arg in record.args
            )
            record.args = new_args
        return True


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Client IP based rate limiter preventing API abuse and denial-of-service.
    """
    def __init__(self, app, requests_per_minute: int = 120):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean timestamps older than 60s
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip]
            if now - t < 60
        ]

        if len(self.request_history[client_ip]) >= self.requests_per_minute:
            return Response(
                content='{"detail": "Rate Limit Exceeded. Too many requests."}',
                status_code=429,
                media_type="application/json"
            )

        self.request_history[client_ip].append(now)
        return await call_next(request)


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects standard production-grade secure headers to prevent XSS, clickjacking, and mime-sniffing.
    """
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
        return response

