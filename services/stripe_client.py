"""
Stripe Client for Replit Integration
Fetches Stripe credentials from Replit's connector API
"""

import os

import requests  # type: ignore[import-untyped]
import stripe

_connection_settings = None


def get_stripe_credentials():
    """
    Fetch Stripe credentials from Replit's connector API.
    Returns (publishable_key, secret_key) tuple.
    """
    global _connection_settings

    hostname = os.environ.get("REPLIT_CONNECTORS_HOSTNAME")

    repl_identity = os.environ.get("REPL_IDENTITY")
    web_repl_renewal = os.environ.get("WEB_REPL_RENEWAL")

    if repl_identity:
        x_replit_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_replit_token = f"depl {web_repl_renewal}"
    else:
        raise ValueError("No REPL_IDENTITY or WEB_REPL_RENEWAL token found")

    if not hostname:
        raise ValueError("REPLIT_CONNECTORS_HOSTNAME not found")

    is_production = os.environ.get("REPLIT_DEPLOYMENT") == "1"
    target_environment = "production" if is_production else "development"

    url = f"https://{hostname}/api/v2/connection"
    params = {
        "include_secrets": "true",
        "connector_names": "stripe",
        "environment": target_environment,
    }

    headers = {"Accept": "application/json", "X_REPLIT_TOKEN": x_replit_token}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    _connection_settings = data.get("items", [{}])[0] if data.get("items") else None

    if not _connection_settings:
        raise ValueError(f"Stripe {target_environment} connection not found")

    settings = _connection_settings.get("settings", {})
    publishable_key = settings.get("publishable")
    secret_key = settings.get("secret")

    if not publishable_key or not secret_key:
        raise ValueError(f"Stripe {target_environment} credentials incomplete")

    return publishable_key, secret_key


def get_stripe_client():
    """
    Get a configured Stripe client with the secret key.
    Returns a configured stripe module.
    """
    _, secret_key = get_stripe_credentials()
    stripe.api_key = secret_key
    return stripe


def get_stripe_publishable_key():
    """Get the Stripe publishable key for client-side use."""
    publishable_key, _ = get_stripe_credentials()
    return publishable_key


def get_stripe_secret_key():
    """Get the Stripe secret key for server-side operations."""
    _, secret_key = get_stripe_credentials()
    return secret_key


def get_webhook_secret():
    """
    Get the webhook signing secret.
    For managed webhooks via Replit, we use the processWebhook approach
    which handles signature verification internally.
    Returns None if not using manual webhook secrets.
    """
    return os.environ.get("STRIPE_WEBHOOK_SECRET")


PRICING_TIERS = {
    "free": {
        "name": "Basic Analysis",
        "amount": 0,
        "display": "FREE",
        "description": "Free credit analysis of negatives only",
        "features": [
            "Negative item identification",
            "Basic violation scan",
            "Credit score factors",
        ],
    },
    "tier1": {
        "name": "Starter",
        "amount": 30000,
        "display": "$300",
        "description": "Entry-level credit restoration",
        "features": ["Full FCRA analysis", "Round 1 dispute letters", "Basic support"],
    },
    "tier2": {
        "name": "Standard",
        "amount": 60000,
        "display": "$600",
        "description": "Complete credit restoration package",
        "features": [
            "Full FCRA analysis",
            "Rounds 1-2 dispute letters",
            "Violation documentation",
            "Email support",
        ],
    },
    "tier3": {
        "name": "Premium",
        "amount": 90000,
        "display": "$900",
        "description": "Advanced litigation-ready package",
        "features": [
            "Full FCRA analysis",
            "Rounds 1-3 dispute letters",
            "Willfulness assessment",
            "Damages calculation",
            "Priority support",
        ],
    },
    "tier4": {
        "name": "Professional",
        "amount": 120000,
        "display": "$1,200",
        "description": "Full litigation package",
        "features": [
            "Complete forensic analysis",
            "All 4 dispute rounds",
            "Settlement demand letter",
            "Litigation documentation",
            "Dedicated support",
        ],
    },
    "tier5": {
        "name": "Elite",
        "amount": 150000,
        "display": "$1,500",
        "description": "Maximum recovery package",
        "features": [
            "Everything in Professional",
            "Attorney coordination",
            "Contingency prep",
            "Unlimited revisions",
            "VIP support",
        ],
    },
}


def create_checkout_session(
    draft_id, tier_key, success_url, cancel_url, customer_email=None
):
    """
    Create a Stripe Checkout session for payment.

    Args:
        draft_id: The SignupDraft UUID to associate with this payment
        tier_key: The pricing tier key (tier1-tier5)
        success_url: URL to redirect on successful payment
        cancel_url: URL to redirect on cancelled payment
        customer_email: Optional email to prefill

    Returns:
        Stripe Checkout Session object
    """
    stripe_client = get_stripe_client()

    tier = PRICING_TIERS.get(tier_key)
    if not tier:
        raise ValueError(f"Invalid pricing tier: {tier_key}")

    session_params = {
        "payment_method_types": ["card", "us_bank_account"],
        "payment_method_options": {
            "us_bank_account": {
                "financial_connections": {
                    "permissions": ["payment_method"],
                },
                "verification_method": "instant",
            },
        },
        "mode": "payment",
        "line_items": [
            {
                "price_data": {
                    "currency": "usd",
                    "unit_amount": tier["amount"],
                    "product_data": {
                        "name": f'FCRA Credit Restoration - {tier["name"]} Plan',
                        "description": "Professional credit restoration services including FCRA analysis, dispute letter generation, and ongoing support.",
                    },
                },
                "quantity": 1,
            }
        ],
        "metadata": {
            "draft_id": draft_id,
            "tier": tier_key,
        },
        "success_url": success_url,
        "cancel_url": cancel_url,
    }

    if customer_email:
        session_params["customer_email"] = customer_email

    session = stripe_client.checkout.Session.create(**session_params)
    return session


def verify_webhook_signature(payload, sig_header, webhook_secret=None):
    """
    Verify the Stripe webhook signature.

    Args:
        payload: Raw request body (bytes)
        sig_header: Stripe-Signature header value
        webhook_secret: Webhook signing secret (optional, uses env var if not provided)

    Returns:
        Stripe Event object if valid

    Raises:
        stripe.error.SignatureVerificationError if invalid
    """
    stripe_client = get_stripe_client()

    if webhook_secret is None:
        webhook_secret = get_webhook_secret()

    if webhook_secret:
        event = stripe_client.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    else:
        import json

        event_data = json.loads(payload)
        event = stripe.Event.construct_from(event_data, stripe.api_key)

    return event


def retrieve_checkout_session(session_id):
    """Retrieve a Checkout Session by ID."""
    stripe_client = get_stripe_client()
    return stripe_client.checkout.Session.retrieve(session_id)
