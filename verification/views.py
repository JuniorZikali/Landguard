from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import log_action

from .deed_checker import check_deed
from .forms import DeedCheckForm, FraudReportForm
from .models import VerificationRequest, FraudReport
from .report_generator import generate_buyer_report


def deed_check_view(request):
    """
    Public title deed authenticity checker. (Objective 2)
    Anyone — even unauthenticated visitors — can use this; it's the
    headline feature.
    """
    result = None
    form = DeedCheckForm(request.GET or None) if request.GET else DeedCheckForm()
    if request.GET and form.is_valid():
        result = check_deed(
            form.cleaned_data['deed_number'],
            form.cleaned_data.get('claimed_owner_id') or None,
            form.cleaned_data.get('claimed_address') or None,
        )
        if request.user.is_authenticated:
            log_action(
                request.user, 'deed_check', 'related_property',
                result['related_property'].id if result['related_property'] else None,
                description=f"Checked deed {result['deed_number']}",
                request=request,
            )
    return render(request, 'verification/deed_check.html', {
        'form': form, 'result': result,
    })


@login_required
def buyer_report_view(request):
    """
    Buyer-facing on-demand fraud risk report. (Objective 3)
    Buyer types in deed details; system returns combined risk report.
    """
    report = None
    form = DeedCheckForm(request.GET or None) if request.GET else DeedCheckForm()
    if request.GET and form.is_valid():
        report = generate_buyer_report(
            form.cleaned_data['deed_number'],
            form.cleaned_data.get('claimed_owner_id') or None,
            form.cleaned_data.get('claimed_address') or None,
        )
        # Persist the request for record-keeping
        VerificationRequest.objects.create(
            buyer=request.user,
            related_property=report['related_property'],
            queried_deed_number=form.cleaned_data['deed_number'],
            queried_owner_id=form.cleaned_data.get('claimed_owner_id') or '',
            queried_address=form.cleaned_data.get('claimed_address') or '',
            risk_level=report['risk_level'],
            risk_score=report['risk_score'],
            authenticity_score=report['authenticity_score'],
            findings=report['deed_findings'],
            report_summary=report['summary'],
        )
        log_action(
            request.user, 'buyer_report', 'related_property',
            report['related_property'].id if report['related_property'] else None,
            description=f"Buyer requested report for {report['deed_number']}",
            request=request,
        )
    return render(request, 'verification/buyer_report.html', {
        'form': form, 'report': report,
    })


@login_required
def my_verifications(request):
    requests = VerificationRequest.objects.filter(buyer=request.user)
    return render(request, 'verification/my_verifications.html', {
        'requests': requests,
    })


@login_required
def fraud_report_create(request):
    if request.method == 'POST':
        form = FraudReportForm(request.POST, request.FILES)
        if form.is_valid():
            fr = form.save(commit=False)
            fr.reported_by = request.user
            fr.save()
            log_action(
                request.user, 'fraud_report', 'FraudReport', fr.id,
                description='Citizen filed fraud report',
                request=request,
            )
            messages.success(
                request,
                'Thank you. Your fraud report has been received and will be reviewed.',
            )
            return redirect('verification:fraud_report_thanks')
    else:
        form = FraudReportForm()
    return render(request, 'verification/fraud_report_form.html', {'form': form})


def fraud_report_thanks(request):
    return render(request, 'verification/fraud_report_thanks.html')
