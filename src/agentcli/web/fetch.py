from __future__ import annotations

import html
import ipaddress
import re
import socket
from urllib.parse import urlparse

import httpx


class NetworkPolicyError(ValueError):
    pass


async def fetch_url(url: str, max_length: int = 10_000, timeout: float = 15.0) -> str:
    current_url = httpx.URL(url)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for _ in range(11):
            _validate_public_url(str(current_url))
            response = await client.get(
                current_url,
                headers={"user-agent": "AgentCLI-Python/0.1.0"},
            )
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise NetworkPolicyError("redirect response is missing a location")
                current_url = response.url.join(location)
                continue

            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            text = response.text
            if "html" in content_type:
                text = extract_text_from_html(text)
            if len(text) > max_length:
                text = text[:max_length] + "\n... [truncated]"
            return text or "(empty page)"
    raise NetworkPolicyError("too many redirects")


def extract_text_from_html(raw_html: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", raw_html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise NetworkPolicyError("only http/https URLs are allowed")
    if not parsed.hostname:
        raise NetworkPolicyError("URL must include a hostname")
    host = parsed.hostname
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        _reject_private_ip(ip)
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise NetworkPolicyError(f"cannot resolve host: {host}") from exc
    for info in infos:
        address = info[4][0]
        try:
            resolved_ip = ipaddress.ip_address(address)
        except ValueError:
            continue
        _reject_private_ip(resolved_ip)


def _reject_private_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
        raise NetworkPolicyError("URL resolves to a private or local address")
