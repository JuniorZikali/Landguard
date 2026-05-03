from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from properties.models import Property
from transactions.models import Transaction, RiskFlag
from verification.models import VerificationRequest, FraudReport


@login_required
def dashboard_home(request):
    profile = request.user.profile
    role = profile.role

    context = {'profile': profile, 'role': role}

    if role in ('registrar', 'admin'):
        context.update({
            'total_properties': Property.objects.count(),
            'flagged_properties': Property.objects.filter(
                status__in=['flagged', 'disputed']
            ).count(),
            'total_transactions': Transaction.objects.count(),
            'high_risk_transactions': Transaction.objects.filter(
                risk_level='HIGH'
            ).count(),
            'recent_transactions': Transaction.objects
                .select_related('related_property', 'seller__profile')
                .order_by('-listed_at')[:5],
            'recent_flags': RiskFlag.objects
                .select_related('transaction__related_property')
                .order_by('-flagged_at')[:5],
            'open_fraud_reports': FraudReport.objects.filter(
                status='open'
            ).count(),
        })
        template = 'dashboard/registrar.html'

    elif role == 'seller':
        my_txns = Transaction.objects.filter(seller=request.user)
        context.update({
            'my_listings': my_txns.count(),
            'my_active_listings': my_txns.filter(
                status__in=['listed', 'pending']
            ).count(),
            'my_flagged_listings': my_txns.filter(risk_level='HIGH').count(),
            'recent_listings': my_txns.select_related('related_property')[:5],
            'my_properties': Property.objects.filter(
                registered_owner=request.user
            ).count(),
        })
        template = 'dashboard/seller.html'

    else:  # buyer (default)
        my_verifications = VerificationRequest.objects.filter(
            buyer=request.user
        )
        context.update({
            'my_verifications_count': my_verifications.count(),
            'recent_verifications': my_verifications[:5],
            'high_risk_warnings': my_verifications.filter(
                risk_level='HIGH'
            ).count(),
        })
        template = 'dashboard/buyer.html'

    return render(request, template, context)