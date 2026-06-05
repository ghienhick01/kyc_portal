import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator

from .models import KYCApplication, KYCDocument, AuditLog
from .forms import KYCApplicationForm, DocumentUploadForm, ReviewForm

audit_logger = logging.getLogger('kyc.audit')


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')


def log_audit(request, action, target_type, target_id, description, extra=None):
    """Create both DB and file audit log entries."""
    ip = get_client_ip(request)
    AuditLog.objects.create(
        actor=request.user,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        description=description,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        extra_data=extra or {}
    )
    audit_logger.info(
        f"User={request.user.username} | Action={action} | "
        f"Target={target_type}:{target_id} | IP={ip} | {description}"
    )


@login_required
def dashboard(request):
    """Main dashboard - role-based view."""
    user = request.user

    if user.is_reviewer:
        # Reviewers see all applications with filters
        applications = KYCApplication.objects.select_related('owner', 'assigned_reviewer').all()

        # Filters
        status_filter = request.GET.get('status', '')
        risk_filter = request.GET.get('risk', '')
        search = request.GET.get('search', '')

        if status_filter:
            applications = applications.filter(status=status_filter)
        if risk_filter:
            applications = applications.filter(risk_level=risk_filter)
        if search:
            applications = applications.filter(
                Q(full_name__icontains=search) |
                Q(owner__username__icontains=search) |
                Q(owner__email__icontains=search)
            )

        paginator = Paginator(applications, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        # Stats
        stats = {
            'total': KYCApplication.objects.count(),
            'pending': KYCApplication.objects.filter(status__in=['submitted', 'under_review']).count(),
            'approved': KYCApplication.objects.filter(status='approved').count(),
            'rejected': KYCApplication.objects.filter(status='rejected').count(),
        }

        recent_logs = AuditLog.objects.select_related('actor').order_by('-timestamp')[:10]

        return render(request, 'kyc/reviewer_dashboard.html', {
            'page_obj': page_obj,
            'stats': stats,
            'recent_logs': recent_logs,
            'status_filter': status_filter,
            'risk_filter': risk_filter,
            'search': search,
            'status_choices': KYCApplication.Status.choices,
            'risk_choices': KYCApplication.RiskLevel.choices,
        })
    else:
        # Applicant: only their own data (Anti-IDOR)
        try:
            application = KYCApplication.objects.get(owner=request.user)
        except KYCApplication.DoesNotExist:
            application = None

        return render(request, 'kyc/applicant_dashboard.html', {
            'application': application,
        })


@login_required
def application_create(request):
    """Create a new KYC application."""
    # Prevent duplicate applications
    if KYCApplication.objects.filter(owner=request.user).exists():
        messages.warning(request, 'You already have an active KYC application.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = KYCApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.owner = request.user
            app.save()
            log_audit(request, 'create', 'KYCApplication', app.public_id,
                      f"New KYC application created by {request.user.username}")
            messages.success(request, 'KYC application created successfully!')
            return redirect('application_detail', public_id=app.public_id)
    else:
        form = KYCApplicationForm()

    return render(request, 'kyc/application_form.html', {'form': form, 'action': 'Create'})


@login_required
def application_detail(request, public_id):
    """View application detail - enforces Anti-IDOR."""
    application = get_object_or_404(KYCApplication, public_id=public_id)

    # ─── ANTI-IDOR CHECK ───────────────────────────────────────────────────
    if not request.user.is_reviewer and application.owner != request.user:
        audit_logger.warning(
            f"IDOR ATTEMPT: User {request.user.username} tried to access "
            f"application {public_id} owned by {application.owner.username}"
        )
        return HttpResponseForbidden(
            render(request, 'kyc/403.html', {'message': 'Access denied. This action has been logged.'})
        )

    # Audit log - Step 3 from security guide
    log_audit(request, 'view', 'KYCApplication', public_id,
              f"User {request.user.username} viewed application {public_id}")

    documents = application.documents.all()
    doc_form = DocumentUploadForm()
    review_form = ReviewForm(instance=application) if request.user.is_reviewer else None
    audit_trail = AuditLog.objects.filter(
        target_type='KYCApplication',
        target_id=str(public_id)
    ).select_related('actor')[:20]

    return render(request, 'kyc/application_detail.html', {
        'application': application,
        'documents': documents,
        'doc_form': doc_form,
        'review_form': review_form,
        'audit_trail': audit_trail,
    })


@login_required
def application_edit(request, public_id):
    """Edit application - only owner, only in draft/additional_info status."""
    application = get_object_or_404(KYCApplication, public_id=public_id)

    # Anti-IDOR
    if application.owner != request.user:
        return HttpResponseForbidden()

    if application.status not in ['draft', 'additional_info']:
        messages.error(request, 'Application cannot be edited in its current status.')
        return redirect('application_detail', public_id=public_id)

    if request.method == 'POST':
        form = KYCApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            log_audit(request, 'update', 'KYCApplication', public_id,
                      f"Application updated by {request.user.username}")
            messages.success(request, 'Application updated successfully.')
            return redirect('application_detail', public_id=public_id)
    else:
        form = KYCApplicationForm(instance=application)

    return render(request, 'kyc/application_form.html', {
        'form': form, 'application': application, 'action': 'Edit'
    })


@login_required
def application_submit(request, public_id):
    """Submit application for review."""
    application = get_object_or_404(KYCApplication, public_id=public_id)

    # Anti-IDOR
    if application.owner != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        if application.documents.count() == 0:
            messages.error(request, 'Please upload at least one document before submitting.')
            return redirect('application_detail', public_id=public_id)

        application.status = KYCApplication.Status.SUBMITTED
        application.submitted_at = timezone.now()
        application.save()

        log_audit(request, 'submit', 'KYCApplication', public_id,
                  f"Application submitted by {request.user.username}")
        messages.success(request, 'Application submitted for review!')
        return redirect('application_detail', public_id=public_id)

    return redirect('application_detail', public_id=public_id)


@login_required
def document_upload(request, public_id):
    """Upload a document to a KYC application."""
    application = get_object_or_404(KYCApplication, public_id=public_id)

    # Anti-IDOR
    if not request.user.is_reviewer and application.owner != request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.application = application
            uploaded_file = request.FILES.get('file')
            if uploaded_file:
                doc.file_name = uploaded_file.name
                doc.file_size = uploaded_file.size
                doc.mime_type = uploaded_file.content_type
            doc.save()

            log_audit(request, 'upload', 'KYCDocument', doc.public_id,
                      f"Document '{doc.get_document_type_display()}' uploaded for application {public_id}",
                      extra={'document_type': doc.document_type, 'file_size': doc.file_size})
            messages.success(request, f'Document uploaded: {doc.get_document_type_display()}')
        else:
            messages.error(request, 'Document upload failed. Please check the file.')

    return redirect('application_detail', public_id=public_id)


@login_required
def document_delete(request, doc_public_id):
    """Delete a document."""
    doc = get_object_or_404(KYCDocument, public_id=doc_public_id)
    application = doc.application

    # Anti-IDOR
    if application.owner != request.user and not request.user.is_reviewer:
        return HttpResponseForbidden()

    if request.method == 'POST':
        log_audit(request, 'delete', 'KYCDocument', doc_public_id,
                  f"Document deleted: {doc.get_document_type_display()}")
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document removed.')

    return redirect('application_detail', public_id=application.public_id)


@login_required
def review_application(request, public_id):
    """Reviewer: approve/reject/update application."""
    if not request.user.is_reviewer:
        return HttpResponseForbidden()

    application = get_object_or_404(KYCApplication, public_id=public_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('reviewer_notes', '')
        risk = request.POST.get('risk_level', application.risk_level)

        application.reviewer_notes = notes
        application.risk_level = risk
        application.assigned_reviewer = request.user
        application.reviewed_at = timezone.now()

        if action == 'approve':
            application.status = KYCApplication.Status.APPROVED
            application.owner.is_verified_user = True
            application.owner.save(update_fields=['is_verified_user'])
            log_audit(request, 'approve', 'KYCApplication', public_id,
                      f"Application APPROVED by reviewer {request.user.username}")
            messages.success(request, f'Application for {application.full_name} has been approved.')

        elif action == 'reject':
            application.status = KYCApplication.Status.REJECTED
            application.rejection_reason = request.POST.get('rejection_reason', '')
            log_audit(request, 'reject', 'KYCApplication', public_id,
                      f"Application REJECTED by reviewer {request.user.username}",
                      extra={'reason': application.rejection_reason})
            messages.warning(request, f'Application for {application.full_name} has been rejected.')

        elif action == 'request_info':
            application.status = KYCApplication.Status.ADDITIONAL_INFO
            log_audit(request, 'update', 'KYCApplication', public_id,
                      f"Additional info requested by {request.user.username}")
            messages.info(request, 'Additional information has been requested.')

        elif action == 'under_review':
            application.status = KYCApplication.Status.UNDER_REVIEW
            log_audit(request, 'update', 'KYCApplication', public_id,
                      f"Application moved to Under Review by {request.user.username}")

        application.save()

    return redirect('application_detail', public_id=public_id)


@login_required
def audit_log_view(request):
    """Compliance: view full audit log."""
    if not request.user.is_compliance_officer:
        return HttpResponseForbidden()

    logs = AuditLog.objects.select_related('actor').all()

    # Filters
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    if action_filter:
        logs = logs.filter(action=action_filter)
    if user_filter:
        logs = logs.filter(actor__username__icontains=user_filter)

    paginator = Paginator(logs, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'kyc/audit_log.html', {
        'page_obj': page_obj,
        'action_choices': AuditLog.Action.choices,
        'action_filter': action_filter,
        'user_filter': user_filter,
    })
