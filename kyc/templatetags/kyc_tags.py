from django import template
from kyc.forms import DocumentUploadForm

register = template.Library()


@register.inclusion_tag('components/upload_form.html')
def upload_form_fields(application):
    return {
        'form': DocumentUploadForm(),
        'application': application,
    }


@register.filter
def status_icon(status):
    icons = {
        'draft': '✏️',
        'submitted': '📤',
        'under_review': '🔍',
        'additional_info': '❓',
        'approved': '✅',
        'rejected': '❌',
    }
    return icons.get(status, '•')


@register.filter
def risk_color(risk):
    colors = {
        'low': '#10b981',
        'medium': '#f59e0b',
        'high': '#ef4444',
        'critical': '#7c3aed',
    }
    return colors.get(risk, '#6b7280')


@register.simple_tag
def kyc_completion_class(pct):
    if pct >= 80:
        return 'progress-high'
    elif pct >= 50:
        return 'progress-mid'
    return 'progress-low'
