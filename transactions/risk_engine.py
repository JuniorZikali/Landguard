"""
LandGuard Rule-Based Fraud Detection Engine
============================================

This module implements the rule-based expert system at the core of LandGuard.
It evaluates a property transaction against a series of fraud-detection rules
and produces:

    - a numeric risk score (0–100)
    - a categorical risk level (LOW / MEDIUM / HIGH)
    - a list of specific risk flags with severity and explanations

The rules encode common fraud patterns observed in the Zimbabwean property
market, including land-baron behaviour, double-selling, deed forgery, and
price manipulation.
"""
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone


# Severity-to-score mapping. Tuned so that one HIGH-severity flag alone is
# enough to cross into MEDIUM risk territory, and two HIGH flags push to HIGH.
SEVERITY_WEIGHTS = {
    'LOW': 10,
    'MEDIUM': 25,
    'HIGH': 40,
}

# Thresholds for converting a numeric score to a categorical risk level.
HIGH_RISK_THRESHOLD = 50
MEDIUM_RISK_THRESHOLD = 20


def evaluate_transaction(transaction):
    """
    Run all fraud-detection rules against `transaction`.
    
    Returns a tuple: (risk_score:int, risk_level:str, flags:list[dict])
    where each flag dict has keys: flag_type, severity, description.
    """
    flags = []
    flags.extend(_check_seller_id_mismatch(transaction))
    flags.extend(_check_duplicate_active_listing(transaction))
    flags.extend(_check_recently_transferred(transaction))
    flags.extend(_check_price_below_market(transaction))
    flags.extend(_check_disputed_status(transaction))
    flags.extend(_check_multiple_listings_same_seller(transaction))
    flags.extend(_check_incomplete_record(transaction))
    flags.extend(_check_unverified_owner(transaction))
    
    risk_score = min(100, sum(SEVERITY_WEIGHTS[f['severity']] for f in flags))
    
    if risk_score >= HIGH_RISK_THRESHOLD:
        risk_level = 'HIGH'
    elif risk_score >= MEDIUM_RISK_THRESHOLD:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    return risk_score, risk_level, flags


def apply_evaluation(transaction, save=True):
    """
    Convenience method: evaluate `transaction`, persist its risk fields,
    create the corresponding RiskFlag records, and return the result tuple.
    """
    from .models import RiskFlag  # local import to avoid circular issues
    
    risk_score, risk_level, flags = evaluate_transaction(transaction)
    transaction.risk_score = risk_score
    transaction.risk_level = risk_level
    if risk_level == 'HIGH':
        transaction.status = 'flagged'
    if save:
        transaction.save()
        # Replace old flags with the freshly computed ones.
        transaction.risk_flags.all().delete()
        for f in flags:
            RiskFlag.objects.create(transaction=transaction, **f)
    return risk_score, risk_level, flags


# --------------------------------------------------------------------------
# Individual rule implementations.
# Each returns a list (possibly empty) of flag dicts.
# --------------------------------------------------------------------------

def _check_seller_id_mismatch(transaction):
    """Rule 1: the seller must be the registered owner of the property."""
    if transaction.seller_id != transaction.related_property.registered_owner_id:
        seller_name = _safe_full_name(transaction.seller)
        owner_name = _safe_full_name(transaction.related_property.registered_owner)
        return [{
            'flag_type': 'seller_id_mismatch',
            'severity': 'HIGH',
            'description': (
                f"The seller ({seller_name}) is NOT the registered owner of "
                f"this property. The registry shows {owner_name} as the owner. "
                f"This is the strongest indicator of a fraudulent sale."
            ),
        }]
    return []


def _check_duplicate_active_listing(transaction):
    """Rule 2: a property must not have multiple active listings (double-selling)."""
    from .models import Transaction
    
    other_active = Transaction.objects.filter(
        related_property=transaction.related_property,
        status__in=['listed', 'pending', 'under_review'],
    ).exclude(pk=transaction.pk)
    
    if other_active.exists():
        return [{
            'flag_type': 'duplicate_active_listing',
            'severity': 'HIGH',
            'description': (
                f"This property already has {other_active.count()} other "
                f"active listing(s) in the system. Multiple simultaneous "
                f"listings are a hallmark of double-selling fraud."
            ),
        }]
    return []


def _check_recently_transferred(transaction):
    """Rule 3: a property recently transferred should not be listed again so soon."""
    from .models import Transaction
    
    cutoff = timezone.now() - timedelta(days=30)
    recent = Transaction.objects.filter(
        related_property=transaction.related_property,
        status='completed',
        completed_at__gte=cutoff,
    ).exclude(pk=transaction.pk).exists()
    
    if recent or transaction.related_property.status == 'transferred':
        return [{
            'flag_type': 'recently_transferred',
            'severity': 'HIGH',
            'description': (
                "This property was transferred to a new owner within the last "
                "30 days. It should not be available for sale by the previous "
                "owner."
            ),
        }]
    return []


def _check_price_below_market(transaction):
    """Rule 4: a listed price far below market value is a known fraud pattern."""
    market = transaction.related_property.market_value_estimate
    if market and transaction.listed_price < (market * Decimal('0.5')):
        return [{
            'flag_type': 'price_below_market',
            'severity': 'MEDIUM',
            'description': (
                f"The listed price (USD {transaction.listed_price:,.2f}) is "
                f"less than 50% of the registry's estimated market value "
                f"(USD {market:,.2f}). Suspiciously low pricing is a common "
                f"land-baron tactic used to pressure quick sales."
            ),
        }]
    return []


def _check_disputed_status(transaction):
    """Rule 5: properties with disputed or flagged status should not be sold."""
    if transaction.related_property.status in ('disputed', 'flagged'):
        return [{
            'flag_type': 'disputed_status',
            'severity': 'HIGH',
            'description': (
                f"The property is currently marked as "
                f"'{transaction.related_property.get_status_display()}' in the registry. "
                f"It cannot legitimately be sold until this status is resolved."
            ),
        }]
    return []


def _check_multiple_listings_same_seller(transaction):
    """Rule 6: a single seller listing many properties quickly is a land-baron pattern."""
    from .models import Transaction
    
    cutoff = timezone.now() - timedelta(days=30)
    recent_count = Transaction.objects.filter(
        seller=transaction.seller,
        listed_at__gte=cutoff,
    ).exclude(pk=transaction.pk).count()
    
    if recent_count >= 5:
        return [{
            'flag_type': 'multiple_listings_same_seller',
            'severity': 'MEDIUM',
            'description': (
                f"This seller has listed {recent_count} other properties in "
                f"the last 30 days. This volume is unusual for an individual "
                f"private seller and matches the behavioural pattern of land "
                f"barons illegally subdividing and reselling land."
            ),
        }]
    return []


def _check_incomplete_record(transaction):
    """Rule 7: a property record missing critical data is harder to verify."""
    p = transaction.related_property
    missing = []
    if not p.gps_latitude or not p.gps_longitude:
        missing.append("GPS coordinates")
    if not p.size_sqm:
        missing.append("size")
    if not p.market_value_estimate:
        missing.append("market value estimate")
    if missing:
        return [{
            'flag_type': 'incomplete_record',
            'severity': 'LOW',
            'description': (
                f"The property record is missing: {', '.join(missing)}. "
                f"Incomplete records reduce verification confidence."
            ),
        }]
    return []


def _check_unverified_owner(transaction):
    """Rule 8: ownership claims by unverified users carry extra risk."""
    owner = transaction.related_property.registered_owner
    if hasattr(owner, 'profile') and not owner.profile.is_verified:
        return [{
            'flag_type': 'unverified_owner',
            'severity': 'LOW',
            'description': (
                "The registered owner's identity has not yet been verified by "
                "a Registrar. This does not by itself prove fraud, but it "
                "reduces verification confidence."
            ),
        }]
    return []


def _safe_full_name(user):
    if hasattr(user, 'profile'):
        return f"{user.profile.full_name} (ID: {user.profile.national_id})"
    return user.get_username()
