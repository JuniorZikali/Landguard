"""
LandGuard Title Deed Authenticity Checker
==========================================

Implements Objective 2: validates a title deed number and detects mismatched
details against the registry.

Zimbabwe title deeds typically follow patterns like:
    1234/2020             (sequential number / year)
    DT 1234/2020          (Deed of Transfer prefix)
    DGT 1234/2020         (Deed of Grant of Township prefix)

This module performs:
    1. Format validation (regex-based syntactic check)
    2. Registry lookup (does this deed exist in our records?)
    3. Cross-field validation (do claimed details match registered details?)
    4. Status check (is the property disputed/flagged?)
    5. Authenticity score (0–100) for buyer-friendly reporting
"""
import re

from properties.models import Property


DEED_PATTERN = re.compile(
    r'^(DT|DGT|DG|DOT)?\s*\d{1,7}\s*[/\-]\s*(19|20)\d{2}$',
    re.IGNORECASE,
)


def normalise(s):
    """Lower-case, strip whitespace and dashes for fuzzy comparison."""
    return ''.join(c for c in (s or '').lower() if c.isalnum())


def check_deed(deed_number, claimed_owner_id=None, claimed_address=None):
    """
    Run the full authenticity check on a title deed number.
    
    Args:
        deed_number: the deed number to verify (string)
        claimed_owner_id: optional national ID the seller claims to have
        claimed_address: optional address the seller claims for the property
    
    Returns:
        dict with keys:
            deed_number          — the cleaned deed number
            is_valid_format      — True/False
            exists_in_registry   — True/False
            property             — Property instance or None
            findings             — list of human-readable issue strings
            authenticity_score   — int 0..100 (higher = more authentic)
    """
    findings = []
    deed_number = (deed_number or '').strip().upper()
    
    is_valid_format = bool(DEED_PATTERN.match(deed_number))
    if not is_valid_format:
        findings.append(
            "Deed number format does not match the standard Zimbabwe title "
            "deed format (e.g. '1234/2020' or 'DT 1234/2020')."
        )
    
    try:
        property_obj = Property.objects.select_related(
            'registered_owner__profile'
        ).get(title_deed_number__iexact=deed_number)
        exists_in_registry = True
    except Property.DoesNotExist:
        property_obj = None
        exists_in_registry = False
        findings.append(
            "This deed number is not in the LandGuard registry. The deed may "
            "either be unregistered, expired, or fraudulent. Verify with the "
            "Deeds Office before proceeding with any payment."
        )
    
    if property_obj:
        if property_obj.status == 'disputed':
            findings.append(
                "The property is currently marked as DISPUTED in the registry."
            )
        elif property_obj.status == 'flagged':
            findings.append(
                "The property has been FLAGGED for suspicious activity in the "
                "registry."
            )
        elif property_obj.status == 'transferred':
            findings.append(
                "The property has been TRANSFERRED. The previous owner can no "
                "longer legitimately sell it."
            )
        
        if claimed_owner_id:
            actual_id = property_obj.registered_owner.profile.national_id
            if normalise(actual_id) != normalise(claimed_owner_id):
                findings.append(
                    "The national ID provided does NOT match the registered "
                    "owner of this property. This is a strong fraud indicator."
                )
        
        if claimed_address:
            registered = property_obj.full_address.lower()
            claimed = claimed_address.lower()
            tokens = [t for t in re.split(r'[\s,]+', claimed) if len(t) > 2]
            if tokens:
                hits = sum(1 for t in tokens if t in registered)
                if hits / len(tokens) < 0.5:
                    findings.append(
                        f"The address provided does not closely match the "
                        f"registered address: '{property_obj.full_address}'."
                    )
    
    score = 100
    if not is_valid_format:
        score -= 30
    if not exists_in_registry:
        score -= 60
    extra_findings = max(
        0,
        len(findings) - (0 if is_valid_format else 1) - (0 if exists_in_registry else 1),
    )
    score -= 15 * extra_findings
    score = max(0, score)
    
    return {
        'deed_number': deed_number,
        'is_valid_format': is_valid_format,
        'exists_in_registry': exists_in_registry,
        'related_property': property_obj,
        'findings': findings,
        'authenticity_score': score,
    }
