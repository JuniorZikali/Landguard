from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from accounts.models import log_action
from properties.models import Property

from .forms import TransactionForm
from .models import Transaction
from .risk_engine import apply_evaluation


@login_required
def transaction_list(request):
    """List transactions visible to the current user (their own + admin sees all)."""
    profile = request.user.profile
    qs = Transaction.objects.select_related(
        'related_property', 'seller__profile', 'buyer__profile'
    )
    if profile.role in ('registrar', 'admin'):
        pass  # see all
    else:
        qs = qs.filter(seller=request.user)
    
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'transactions/list.html', {'page_obj': page_obj})


@login_required
def transaction_detail(request, pk):
    txn = get_object_or_404(
        Transaction.objects.select_related(
            'related_property', 'seller__profile', 'buyer__profile',
        ).prefetch_related('risk_flags'),
        pk=pk,
    )
    return render(request, 'transactions/detail.html', {'transaction': txn})


@login_required
def transaction_create(request):
    """Seller lists a property — risk engine runs immediately on submit."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            txn = form.save(commit=False)
            txn.seller = request.user
            txn.save()
            risk_score, risk_level, flags = apply_evaluation(txn)
            log_action(
                request.user, 'create_transaction', 'Transaction', txn.id,
                description=(
                    f'Listed {txn.related_property} at USD {txn.listed_price}. '
                    f'Risk: {risk_level} ({risk_score}). Flags: {len(flags)}.'
                ),
                request=request,
            )
            if risk_level == 'HIGH':
                messages.warning(
                    request,
                    f'Listing created, but flagged as HIGH risk '
                    f'(score {risk_score}). It has been sent for review.',
                )
            else:
                messages.success(
                    request,
                    f'Listing created. Risk level: {risk_level} (score {risk_score}).',
                )
            return redirect('transactions:detail', pk=txn.pk)
    else:
        form = TransactionForm()
        # Restrict the property dropdown to active properties
        form.fields['related_property'].queryset = Property.objects.filter(status='active')
    return render(request, 'transactions/form.html', {'form': form})
