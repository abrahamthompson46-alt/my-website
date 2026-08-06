from django.conf import settings

from payments.constants import FLUTTERWAVE, HUBTEL, MANUAL, PAYSTACK
from payments.gateways.base import BasePaymentGateway
from payments.gateways.exceptions import PaymentGatewayError
from payments.gateways.flutterwave import FlutterwaveGateway
from payments.gateways.hubtel import HubtelGateway
from payments.gateways.manual import ManualGateway
from payments.gateways.paystack import PaystackGateway

GATEWAY_CLASSES: dict[str, type[BasePaymentGateway]] = {
    PAYSTACK: PaystackGateway,
    HUBTEL: HubtelGateway,
    FLUTTERWAVE: FlutterwaveGateway,
    MANUAL: ManualGateway,
}


def get_gateway_class(code: str) -> type[BasePaymentGateway]:
    gateway_cls = GATEWAY_CLASSES.get(code)
    if not gateway_cls:
        raise PaymentGatewayError(f"Unknown payment gateway: {code}")
    return gateway_cls


def get_gateway(code: str, config: dict | None = None) -> BasePaymentGateway:
    gateway_cls = get_gateway_class(code)
    merged_config = _merge_settings_config(code, config or {})
    return gateway_cls(merged_config)


def get_gateway_from_model(gateway_config) -> BasePaymentGateway:
    config = {
        "enabled": gateway_config.is_active,
        **gateway_config.settings,
    }
    env_config = _merge_settings_config(gateway_config.code, {})
    config.update({k: v for k, v in env_config.items() if v})
    return get_gateway(gateway_config.code, config)


def list_available_gateways(active_only=True):
    from payments.models import GatewayConfiguration

    qs = GatewayConfiguration.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("-is_default", "name")


def _merge_settings_config(code: str, config: dict) -> dict:
    settings_map = getattr(settings, "PAYMENTS_GATEWAYS", {})
    gateway_settings = settings_map.get(code, {})
    merged = {**gateway_settings, **config}
    merged.setdefault("enabled", bool(gateway_settings.get("enabled", code == MANUAL)))
    return merged
