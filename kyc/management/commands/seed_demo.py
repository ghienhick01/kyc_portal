"""
Management command: python manage.py seed_demo
Creates demo users for all roles + sample KYC applications.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from kyc.models import KYCApplication, AuditLog
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with demo users and KYC applications'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding demo data...')

        # ── Admin ──
        admin, _ = User.objects.get_or_create(username='admin')
        admin.set_password('admin123!')
        admin.role = 'admin'
        admin.email = 'admin@verifyid.demo'
        admin.first_name = 'System'
        admin.last_name = 'Admin'
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        self.stdout.write(f'  ✓ Admin user: admin / admin123!')

        # ── Compliance Officer ──
        compliance, _ = User.objects.get_or_create(username='compliance_officer')
        compliance.set_password('comply123!')
        compliance.role = 'compliance'
        compliance.email = 'compliance@verifyid.demo'
        compliance.first_name = 'Maria'
        compliance.last_name = 'Santos'
        compliance.save()
        self.stdout.write(f'  ✓ Compliance officer: compliance_officer / comply123!')

        # ── KYC Reviewer ──
        reviewer, _ = User.objects.get_or_create(username='kyc_reviewer')
        reviewer.set_password('review123!')
        reviewer.role = 'reviewer'
        reviewer.email = 'reviewer@verifyid.demo'
        reviewer.first_name = 'Jose'
        reviewer.last_name = 'Reyes'
        reviewer.save()
        self.stdout.write(f'  ✓ Reviewer: kyc_reviewer / review123!')

        # ── Applicants ──
        applicants_data = [
            {
                'username': 'juan_dela_cruz',
                'password': 'applicant123!',
                'email': 'juan@example.com',
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'full_name': 'Juan Dela Cruz',
                'nationality': 'Filipino',
                'city': 'Manila',
                'country': 'Philippines',
                'status': 'submitted',
                'risk_level': 'low',
            },
            {
                'username': 'maria_reyes',
                'password': 'applicant123!',
                'email': 'maria@example.com',
                'first_name': 'Maria',
                'last_name': 'Reyes',
                'full_name': 'Maria Reyes',
                'nationality': 'Filipino',
                'city': 'Cebu City',
                'country': 'Philippines',
                'status': 'approved',
                'risk_level': 'low',
            },
            {
                'username': 'pedro_garcia',
                'password': 'applicant123!',
                'email': 'pedro@example.com',
                'first_name': 'Pedro',
                'last_name': 'Garcia',
                'full_name': 'Pedro Garcia',
                'nationality': 'Filipino',
                'city': 'Davao',
                'country': 'Philippines',
                'status': 'under_review',
                'risk_level': 'medium',
            },
            {
                'username': 'lisa_tan',
                'password': 'applicant123!',
                'email': 'lisa@example.com',
                'first_name': 'Lisa',
                'last_name': 'Tan',
                'full_name': 'Lisa Tan',
                'nationality': 'Filipino',
                'city': 'Quezon City',
                'country': 'Philippines',
                'status': 'draft',
                'risk_level': 'low',
            },
        ]

        for data in applicants_data:
            user, _ = User.objects.get_or_create(username=data['username'])
            user.set_password(data['password'])
            user.role = 'applicant'
            user.email = data['email']
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            if data['status'] == 'approved':
                user.is_verified_user = True
            user.save()

            app, created = KYCApplication.objects.get_or_create(owner=user)
            if created:
                import datetime, uuid
                app.full_name = data['full_name']
                app.nationality = data['nationality']
                app.city = data['city']
                app.country = data['country']
                app.address_line1 = f'123 Sample Street'
                app.postal_code = '1000'
                app.date_of_birth = datetime.date(1990, 1, 15)
                app.status = data['status']
                app.risk_level = data['risk_level']
                if data['status'] in ['submitted', 'under_review', 'approved', 'rejected']:
                    app.submitted_at = timezone.now()
                if data['status'] == 'approved':
                    app.reviewed_at = timezone.now()
                    app.assigned_reviewer = reviewer
                    app.reviewer_notes = 'All documents verified. Identity confirmed.'
                app.save()

                # Create audit log entry
                AuditLog.objects.create(
                    actor=user,
                    action='create',
                    target_type='KYCApplication',
                    target_id=str(app.public_id),
                    description=f'Demo application created for {user.username}',
                    ip_address='127.0.0.1',
                )

            self.stdout.write(f'  ✓ Applicant: {data["username"]} / {data["password"]} [{data["status"]}]')

        self.stdout.write('\n✅ Demo data seeded successfully!')
        self.stdout.write('\n📋 LOGIN CREDENTIALS:')
        self.stdout.write('  Role             | Username             | Password')
        self.stdout.write('  ─────────────────|──────────────────────|─────────────')
        self.stdout.write('  Administrator    | admin                | admin123!')
        self.stdout.write('  Compliance Ofcr  | compliance_officer   | comply123!')
        self.stdout.write('  KYC Reviewer     | kyc_reviewer         | review123!')
        self.stdout.write('  Applicant        | juan_dela_cruz       | applicant123!')
        self.stdout.write('  Applicant        | maria_reyes          | applicant123!')
        self.stdout.write('  Applicant        | pedro_garcia         | applicant123!')
        self.stdout.write('  Applicant        | lisa_tan             | applicant123!')
