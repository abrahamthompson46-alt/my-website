import json
import urllib.error
import urllib.request

from payments.gateways.exceptions import GatewayAPIError, GatewayNotConfiguredError


class HTTPGatewayMixin:
    """Shared HTTP helpers for online payment providers."""

    api_base_url: str = ""

    def _request(self, method, path, data=None, headers=None):
        if not self.is_configured():
            raise GatewayNotConfiguredError(f"{self.code} is not configured.")

        url = f"{self.api_base_url.rstrip('/')}/{path.lstrip('/')}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if headers:
            req_headers.update(headers)

        request = urllib.request.Request(url, data=body, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            raise GatewayAPIError(
                payload.get("message") or str(exc),
                status_code=exc.code,
                response=payload,
            ) from exc
