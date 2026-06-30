"""
Action Agent — email / report / WhatsApp.
All outbound actions require explicit confirmation. Audit-logged.
"""

from __future__ import annotations

import os
import re
import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from typing import Any

from agentkit.a2a.models import A2ATask, AgentCard, AgentSkill
from agentkit.a2a.router import a2a_router
from agentkit.mcp.registry import MCPRegistry
from agentkit.mcp.tool import MCPTool, ToolResult
from agentkit.tracing import trace_span
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
load_dotenv(".env.local", override=True)

_SMTP_HOST = os.getenv("SMTP_HOST", "mailhog")
_SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
_FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@wealthmesh.local")
_FROM_NAME = os.getenv("FROM_NAME", "LaRuche Advisor")
_SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
_SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
_SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "false").lower() in {"1", "true", "yes", "on"}
_SMTP_SSL = os.getenv("SMTP_SSL", "false").lower() in {"1", "true", "yes", "on"}

_TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
_TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN", "")
_TWILIO_WA_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")

_AUDIT_LOG: list[dict[str, Any]] = []
_EMAIL_RE = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{6,}\d")
_CONTENT_MARKER = "Content to send:"


def _is_confirmed(message: str) -> bool:
    return bool(re.search(r"\bconfirmed\s*=\s*true\b", message, re.IGNORECASE))


def _audit(action: str, details: dict[str, Any]) -> None:
    _AUDIT_LOG.append({"timestamp": datetime.now(UTC).isoformat(), "action": action, **details})


def _smtp_hosts() -> list[str]:
    if _SMTP_USERNAME or _SMTP_PASSWORD:
        return [_SMTP_HOST]
    hosts = [_SMTP_HOST]
    for fallback in ("localhost", "127.0.0.1"):
        if fallback not in hosts:
            hosts.append(fallback)
    return hosts


def _smtp_unavailable_message(last_error: Exception) -> str:
    return (
        "Email could not be sent because the SMTP service is unavailable. "
        f"Tried {', '.join(_smtp_hosts())}:{_SMTP_PORT}. "
        "Start MailHog/Docker Desktop for local capture, or configure a real SMTP server "
        f"with SMTP_HOST and SMTP_PORT. Last error: {last_error}"
    )


def _is_local_capture(host: str) -> bool:
    return _SMTP_PORT == 1025 and host in {"mailhog", "localhost", "127.0.0.1"}


def _uses_authenticated_smtp() -> bool:
    return bool(_SMTP_USERNAME or _SMTP_PASSWORD)


def _smtp_connect(host: str) -> smtplib.SMTP:
    if _SMTP_SSL or _SMTP_PORT == 465:
        smtp: smtplib.SMTP = smtplib.SMTP_SSL(host, _SMTP_PORT, timeout=15)
    else:
        smtp = smtplib.SMTP(host, _SMTP_PORT, timeout=15)
        if _SMTP_STARTTLS or _SMTP_PORT == 587:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
    if _SMTP_USERNAME or _SMTP_PASSWORD:
        smtp.login(_SMTP_USERNAME, _SMTP_PASSWORD)
    return smtp


def _plain_to_html(text: str) -> str:
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", text.strip()) if part.strip()]
    if not paragraphs:
        paragraphs = ["Please see your LaRuche advisory update below."]
    body = "\n".join(
        f"<p>{escape(paragraph).replace(chr(10), '<br>')}</p>" for paragraph in paragraphs
    )
    return f"""<!doctype html>
<html>
  <body style="margin:0;background:#062b29;padding:28px;font-family:Inter,Segoe UI,Arial,sans-serif;color:#ecfffb;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;margin:0 auto;background:#082f2d;border:1px solid rgba(53,199,190,.28);border-radius:24px;overflow:hidden;">
      <tr>
        <td style="padding:28px 30px;background:linear-gradient(135deg,#0f4b46,#092f2c);border-bottom:1px solid rgba(255,255,255,.08);">
          <div style="font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#35c7be;font-weight:800;">LaRuche</div>
          <h1 style="margin:8px 0 0;font-size:28px;line-height:1.15;color:#ffffff;">Private Wealth Intelligence</h1>
          <p style="margin:10px 0 0;color:#9ec4bd;font-size:14px;">Advisor summary prepared from your LaRuche assistant conversation.</p>
        </td>
      </tr>
      <tr>
        <td style="padding:28px 30px;">
          <div style="padding:18px 18px;border-radius:18px;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);font-size:15px;line-height:1.75;color:#ecfffb;">
            {body}
          </div>
          <div style="margin-top:20px;padding:14px 16px;border-radius:14px;background:rgba(245,166,35,.12);border:1px solid rgba(245,166,35,.22);color:#ffdca6;font-size:12px;line-height:1.55;">
            LaRuche can make mistakes. Verify important financial information before making decisions.
          </div>
        </td>
      </tr>
      <tr>
        <td style="padding:18px 30px;color:#7da7a0;font-size:12px;border-top:1px solid rgba(255,255,255,.08);">
          Sent by LaRuche Advisor
        </td>
      </tr>
    </table>
  </body>
</html>"""


def _build_email(to: str, subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((_FROM_NAME, _FROM_EMAIL))
    msg["To"] = to
    msg.set_content(body)
    msg.add_alternative(_plain_to_html(body), subtype="html")
    return msg


def _extract_content_to_send(message: str) -> str:
    index = message.lower().find(_CONTENT_MARKER.lower())
    if index == -1:
        return ""

    content = message[index + len(_CONTENT_MARKER) :]
    for marker in ("\n\nResponse format:", "\n\nAdvisor style:", "\nconfirmed=true"):
        marker_index = content.find(marker)
        if marker_index != -1:
            content = content[:marker_index]
    return content.strip()


class ReportBuildTool(MCPTool):
    @property
    def name(self) -> str:
        return "report.build"

    @property
    def description(self) -> str:
        return "Generate a portfolio performance report."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "default": "Valued Client"},
                "format": {"type": "string", "enum": ["text", "html"], "default": "text"},
            },
            "required": [],
        }

    async def execute(
        self,
        client_name: str = "Valued Client",
        format: str = "text",
        **_kw: Any,
    ) -> ToolResult:
        report = (
            f"Portfolio Performance Report — {datetime.now(UTC).strftime('%Y-%m-%d')}\n"
            f"Client: {client_name}\n\n"
            "AUM: $20.4M | TWR: 178.65% | Annualized: 7.14%\n"
            "IRR: 8.30% | Sharpe: 0.58 | Volatility: 12.27%\n"
            "Profit: $7.85M | Deals: 48\n\n"
            "Geography: Asia 37% | NA 35% | Global 16% | Europe 8% | ME 4%\n"
            "Sectors: RE 45% | PE 35% | EQ 15% | Credit 5%\n"
        )
        if format == "html":
            report = f"<pre>{report}</pre>"
        _audit("report.build", {"client": client_name})
        return ToolResult(content=report)


class EmailSendTool(MCPTool):
    @property
    def name(self) -> str:
        return "email.send"

    @property
    def description(self) -> str:
        return "Send an email (MailHog in dev). Requires confirmed=true."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "confirmed": {"type": "boolean", "default": False},
            },
            "required": ["to", "subject", "body"],
        }

    async def execute(
        self,
        to: str = "",
        subject: str = "",
        body: str = "",
        confirmed: bool = False,
        **_kw: Any,
    ) -> ToolResult:
        if not confirmed:
            return ToolResult(content=f"Confirm email to {to}? Set confirmed=true to send.")
        msg = _build_email(to, subject, body)
        last_error: Exception | None = None
        for host in _smtp_hosts():
            try:
                with _smtp_connect(host) as s:
                    s.sendmail(_FROM_EMAIL, [to], msg.as_string())
                _audit(
                    "email.send",
                    {
                        "to": to,
                        "subject": subject,
                        "smtp_host": host,
                        "authenticated": _uses_authenticated_smtp(),
                    },
                )
                if _is_local_capture(host):
                    return ToolResult(
                        content=(
                            f"Email captured in local MailHog for {to}: '{subject}'. "
                            "Open http://localhost:8025 to view it. It was not delivered to the real inbox."
                        ),
                        metadata={"delivery_status": "captured_local", "delivered_to_inbox": False},
                    )
                return ToolResult(
                    content=(
                        f"Email sent to {to}: '{subject}' (accepted by SMTP). "
                        "Delivery to the recipient inbox depends on the SMTP provider."
                    ),
                    metadata={"delivery_status": "accepted_by_smtp", "delivered_to_inbox": None},
                )
            except Exception as exc:
                last_error = exc
        if last_error:
            return ToolResult(
                content=_smtp_unavailable_message(last_error),
                metadata={"delivery_status": "failed", "delivered_to_inbox": False},
            )
        return ToolResult(
            content="Email could not be sent because no SMTP host was available.",
            metadata={"delivery_status": "failed", "delivered_to_inbox": False},
        )


class WhatsAppSendTool(MCPTool):
    @property
    def name(self) -> str:
        return "whatsapp.send"

    @property
    def description(self) -> str:
        return "Send a WhatsApp message (stub). Requires confirmed=true."

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "message": {"type": "string"},
                "confirmed": {"type": "boolean", "default": False},
            },
            "required": ["to", "message"],
        }

    async def execute(
        self,
        to: str = "",
        message: str = "",
        confirmed: bool = False,
        **_kw: Any,
    ) -> ToolResult:
        if not confirmed:
            return ToolResult(content=f"Confirm WhatsApp to {to}? Set confirmed=true.")

        clean_to = re.sub(r"[^\d+]", "", to)
        if not clean_to.startswith("+"):
            clean_to = f"+{clean_to}"

        if not _TWILIO_SID or not _TWILIO_AUTH or not _TWILIO_WA_FROM:
            _audit("whatsapp.send", {"to": clean_to, "status": "no_credentials"})
            return ToolResult(
                content=f"WhatsApp message logged for {clean_to} (Twilio not configured).",
                metadata={"delivery_status": "logged"},
            )

        import httpx

        url = f"https://api.twilio.com/2010-04-01/Accounts/{_TWILIO_SID}/Messages.json"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    auth=(_TWILIO_SID, _TWILIO_AUTH),
                    data={
                        "From": f"whatsapp:{_TWILIO_WA_FROM}",
                        "To": f"whatsapp:{clean_to}",
                        "Body": message or "Your LaRuche portfolio report is ready.",
                    },
                )
            if resp.status_code in (200, 201):
                sid = resp.json().get("sid", "")
                _audit("whatsapp.send", {"to": clean_to, "twilio_sid": sid, "status": "sent"})
                return ToolResult(
                    content=f"WhatsApp message sent to {clean_to}.",
                    metadata={"delivery_status": "sent", "twilio_sid": sid},
                )
            error_msg = resp.json().get("message", resp.text[:200])
            _audit("whatsapp.send", {"to": clean_to, "status": "failed", "error": error_msg})
            return ToolResult(
                content=f"WhatsApp delivery failed: {error_msg}",
                metadata={"delivery_status": "failed"},
            )
        except Exception as exc:
            _audit("whatsapp.send", {"to": clean_to, "status": "error", "error": str(exc)})
            return ToolResult(
                content=f"WhatsApp send error: {exc}",
                metadata={"delivery_status": "error"},
            )


_FINANCIAL_KEYWORDS_RE = re.compile(
    r"\b(?:portfolio|holdings|positions|securities|performance|aum|twr|irr|"
    r"sharpe|volatility|deals|breakdown|sector|geography|allocation|summary|report)\b",
    re.IGNORECASE,
)


def _fetch_portfolio_summary() -> str:
    from agentkit.portfolio import get_metrics
    m = get_metrics()
    return (
        f"Portfolio Summary\n"
        f"AUM: {m['aum_fmt']} ({m['num_deals']} deals, {m['num_active']} active)\n"
        f"Total Profit: {m['profit_fmt']}\n"
        f"ITD TWR: {m['twr_pct']:.2f}%\n"
        f"Annualized Return: {m['annualized_pct']:.2f}%\n"
        f"IRR: {m['irr_pct']:.2f}%\n"
        f"Sharpe Ratio: {m['sharpe']:.2f}\n"
        f"Volatility: {m['volatility_pct']:.2f}%\n"
        f"Inception: {m['years']:.1f} years"
    )


_registry = MCPRegistry()
_registry.register(ReportBuildTool())
_registry.register(EmailSendTool())
_registry.register(WhatsAppSendTool())


_ACTION_KEYWORDS = {"whatsapp", "email", "send", "notify", "report", "export", "share", "download"}


def _edit_distance(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            curr[j] = prev[j - 1] if ca == cb else 1 + min(prev[j], curr[j - 1], prev[j - 1])
        prev = curr
    return prev[-1]


def _fuzzy_lower(msg: str) -> str:
    lower = msg.lower()
    for token in re.findall(r"[a-z]+", lower):
        if len(token) < 4 or token in _ACTION_KEYWORDS:
            continue
        threshold = 1 if len(token) <= 6 else 2
        for kw in _ACTION_KEYWORDS:
            if abs(len(token) - len(kw)) > threshold:
                continue
            if _edit_distance(token, kw) <= threshold:
                lower = lower.replace(token, kw)
                break
    return lower


def _resolve_content(msg: str, content_to_send: str) -> str:
    if content_to_send:
        return content_to_send
    if _FINANCIAL_KEYWORDS_RE.search(msg):
        return _fetch_portfolio_summary()
    return ""


def _pick(msg: str) -> tuple[str, dict[str, Any]]:
    lower = _fuzzy_lower(msg)
    confirmed = _is_confirmed(msg)
    content_to_send = _extract_content_to_send(msg)
    body = _resolve_content(msg, content_to_send)
    if "whatsapp" in lower:
        recipient = _PHONE_RE.search(msg)
        return "whatsapp.send", {
            "to": recipient.group(0).strip() if recipient else "+1234567890",
            "message": body or "Your LaRuche portfolio report is ready.",
            "confirmed": confirmed,
        }
    if "email" in lower or "send" in lower:
        recipient = _EMAIL_RE.search(msg)
        return "email.send", {
            "to": recipient.group(0) if recipient else "client@wealthmesh.local",
            "subject": "LaRuche Portfolio Summary",
            "body": body or "Please see your portfolio report.",
            "confirmed": confirmed,
        }
    return "report.build", {}


async def handle_task(task: A2ATask) -> A2ATask:
    msg = task.messages[-1].content if task.messages else ""
    with trace_span("action_agent", task_id=task.task_id):
        tool_name, kwargs = _pick(msg)
        result = await _registry.call(tool_name, **kwargs)
        answer = result.content if result.ok else f"Error: {result.error}"
    return task.succeed(answer, {"tool": tool_name})


_CARD = AgentCard(
    id="agent-action",
    name="Action Agent",
    description="Report generation, email and WhatsApp delivery.",
    version="0.1.0",
    url="http://agent-action:8004",
    skills=[
        AgentSkill(
            id="chat",
            name="Action Chat",
            description="Execute communication and reporting actions.",
            input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            output_schema={"type": "object", "properties": {"answer": {"type": "string"}}},
        )
    ],
)

app = FastAPI(title="Action Agent", version="0.1.0")
app.include_router(a2a_router(_CARD, handle_task))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "agent-action"}


@app.get("/api/audit-log")
async def audit_log() -> list[dict[str, Any]]:
    return _AUDIT_LOG
