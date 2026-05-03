"""
LandGuard Buyer Fraud Risk Report Generator
============================================

Implements Objective 3: produce on-demand fraud risk reports for buyers.

A buyer supplies a deed number (and optionally the seller's claimed national ID
and address). The system combines:
  - the title deed authenticity checker (Objective 2)
  - any active transactions on the property (the rule-based risk engine)
to produce a unified buyer-friendly report.
"""
from .deed_checker import check_deed


# Combined risk level mapping
_RISK_FROM_AUTHENTICITY = [
    (90, 'LOW'),
    (60, 'MEDIUM'),
    (0,  'HIGH'),
]


def generate_buyer_report(deed_number, claimed_owner_id=None, claimed_address=None):
    """
    Produce a comprehensive fraud risk report for a buyer.
    
    Returns dict with keys:
        deed_number, property, exists_in_registry, is_valid_format,
        authenticity_score, deed_findings, active_transactions,
        transaction_flags, risk_level, risk_score, summary
    """
    from transactions.models import Transaction
    
    deed = check_deed(deed_number, claimed_owner_id, claimed_address)
    
    active_transactions = []
    transaction_flags = []
    
    if deed['related_property']:
        active_transactions = list(
            Transaction.objects.filter(
                related_property=deed['related_property'],
                status__in=['listed', 'pending', 'under_review', 'flagged'],
            ).select_related('seller__profile').prefetch_related('risk_flags')
        )
        for txn in active_transactions:
            for flag in txn.risk_flags.all():
                transaction_flags.append({
                    'flag_type': flag.get_flag_type_display(),
                    'severity': flag.severity,
                    'description': flag.description,
                })
    
    # Combine authenticity score with transaction-based flags into final risk.
    auth_score = deed['authenticity_score']
    base_risk_level = next(
        level for thr, level in _RISK_FROM_AUTHENTICITY if auth_score >= thr
    )
    
    severity_score = {'LOW': 10, 'MEDIUM': 25, 'HIGH': 40}
    txn_score = sum(severity_score.get(f['severity'], 0) for f in transaction_flags)
    
    if base_risk_level == 'HIGH' or txn_score >= 50 or len(active_transactions) > 1:
        risk_level = 'HIGH'
    elif base_risk_level == 'MEDIUM' or txn_score >= 20:
        risk_level = 'MEDIUM'
    else:
        risk_level = 'LOW'
    
    combined_score = min(100, (100 - auth_score) + txn_score)
    
    summary = _build_summary(
        deed=deed,
        active_transactions=active_transactions,
        risk_level=risk_level,
    )
    
    return {
        'deed_number': deed['deed_number'],
        'related_property': deed['related_property'],
        'exists_in_registry': deed['exists_in_registry'],
        'is_valid_format': deed['is_valid_format'],
        'authenticity_score': auth_score,
        'deed_findings': deed['findings'],
        'active_transactions': active_transactions,
        'transaction_flags': transaction_flags,
        'risk_level': risk_level,
        'risk_score': combined_score,
        'summary': summary,
    }


def _build_summary(deed, active_transactions, risk_level):
    """Plain-English summary the buyer can read at a glance."""
    if not deed['exists_in_registry']:
        return (
            "This deed number is NOT in the LandGuard registry. We cannot "
            "verify ownership or authenticity. Do NOT proceed with payment "
            "until you have independently verified the deed at the Deeds "
            "Office in Harare."
        )
    
    prop = deed['related_property']
    if risk_level == 'HIGH':
        return (
            f"HIGH RISK: This property ({prop}) shows multiple serious fraud "
            f"indicators. We strongly advise you do not proceed without "
            f"independent legal verification."
        )
    if risk_level == 'MEDIUM':
        return (
            f"MEDIUM RISK: This property ({prop}) is in the registry but "
            f"shows some warning signs. Proceed with caution and verify all "
            f"details independently before payment."
        )
    if len(active_transactions) > 1:
        return (
            f"HIGH RISK: This property has {len(active_transactions)} active "
            f"listings simultaneously. This is a strong indicator of "
            f"double-selling. Do not proceed."
        )
    return (
        f"LOW RISK: This property ({prop}) is in good standing in the "
        f"LandGuard registry. Always perform your own due diligence at the "
        f"Deeds Office before payment, but no automated red flags were raised."
    )
