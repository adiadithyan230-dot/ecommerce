from .models import AuditLog


def log_action(actor, action, target='', details=''):
    AuditLog.objects.create(
        actor=actor if getattr(actor, 'is_authenticated', False) else None,
        action=action,
        target=str(target or ''),
        details=str(details or ''),
    )
