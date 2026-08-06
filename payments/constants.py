"""Payment gateway codes."""
PAYSTACK = "paystack"
HUBTEL = "hubtel"
FLUTTERWAVE = "flutterwave"
MANUAL = "manual"

GATEWAY_CHOICES = [
    (PAYSTACK, "Paystack"),
    (HUBTEL, "Hubtel"),
    (FLUTTERWAVE, "Flutterwave"),
    (MANUAL, "Manual"),
]

ONLINE_GATEWAYS = {PAYSTACK, HUBTEL, FLUTTERWAVE}
