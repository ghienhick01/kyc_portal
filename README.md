# VerifyID — Digital KYC & Document Verification Portal

> A production-ready, secure enterprise KYC application built with Django, DRF, and modern security practices.

---

## 📁 Project Structure

```
kyc_portal/
├── manage.py
├── requirements.txt
├── Procfile                      # Render/Railway deployment
├── build.sh                      # Cloud build script
├── .env.example                  # Environment variable template
│
├── kyc_portal/                   # Django project config
│   ├── settings.py               # All settings (security, logging, axes, JWT)
│   ├── urls.py                   # Root URL configuration
│   └── wsgi.py
│
├── accounts/                     # Custom user model & auth
│   ├── models.py                 # CustomUser with RBAC roles + field masking
│   ├── views.py                  # Login, register, logout, profile
│   ├── forms.py                  # Auth forms
│   ├── urls.py
│   └── admin.py
│
├── kyc/                          # Core KYC domain
│   ├── models.py                 # KYCApplication, KYCDocument, AuditLog
│   ├── views.py                  # All KYC views (Anti-IDOR enforced)
│   ├── forms.py                  # Application & document forms
│   ├── urls.py
│   ├── admin.py
│   ├── templatetags/
│   │   └── kyc_tags.py           # Custom template tags (Frontend Engineer)
│   └── management/commands/
│       └── seed_demo.py          # Demo data seeder
│
├── api/                          # DRF REST API
│   ├── serializers.py            # JWT-protected serializers w/ field masking
│   ├── views.py                  # API endpoints with RBAC
│   └── urls.py
│
├── templates/
│   ├── base.html                 # Sidebar layout, messages, auth wrapper
│   ├── registration/
│   │   ├── login.html            # Login with security note
│   │   ├── register.html         # Registration with step indicator
│   │   └── lockout.html          # django-axes lockout page
│   ├── accounts/
│   │   └── profile.html
│   ├── kyc/
│   │   ├── applicant_dashboard.html
│   │   ├── reviewer_dashboard.html
│   │   ├── application_detail.html
│   │   ├── application_form.html
│   │   ├── audit_log.html
│   │   └── 403.html
│   └── components/
│       └── upload_form.html      # Reusable upload component
│
├── static/
│   ├── css/main.css              # Full design system (dark theme)
│   └── js/main.js                # Interactive behaviors
│
└── logs/                         # Audit + security log files (auto-created)
```

---

## 🚀 Quick Setup (Local Development)

### 1. Clone & Create Virtual Environment
```bash
git clone <your-repo-url>
cd kyc_portal
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env — set SECRET_KEY, leave DEBUG=True for dev
```

### 4. Initialize Database
```bash
python manage.py migrate
```

### 5. Seed Demo Data
```bash
python manage.py seed_demo
```

### 6. Create Log Directory
```bash
mkdir -p logs
```

### 7. Collect Static Files
```bash
python manage.py collectstatic --no-input
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** — you're live!

---

## 🔑 Demo Login Credentials

| Role              | Username             | Password       | Access Level              |
|-------------------|----------------------|----------------|---------------------------|
| Administrator     | `admin`              | `admin123!`    | Full access + Django admin|
| Compliance Officer| `compliance_officer` | `comply123!`   | Audit logs, all apps      |
| KYC Reviewer      | `kyc_reviewer`       | `review123!`   | Review & approve apps     |
| Applicant         | `juan_dela_cruz`     | `applicant123!`| Submitted application     |
| Applicant         | `maria_reyes`        | `applicant123!`| Approved (verified)       |
| Applicant         | `pedro_garcia`       | `applicant123!`| Under review              |
| Applicant         | `lisa_tan`           | `applicant123!`| Draft application         |

---

## 🛡️ Security Implementation (Per Project Guide)

### Step 1 — Strict Access Control (`@login_required`)
All views in `kyc/views.py` and `accounts/views.py` use `@login_required`.
Unauthenticated users are redirected to `/accounts/login/`.

```python
@login_required
def dashboard(request):
    ...

@login_required
def application_detail(request, public_id):
    ...
```

### Step 2 — Anti-IDOR Logic
- Applications are queried with `filter(owner=request.user)` for applicants
- UUID public IDs instead of sequential integers prevent enumeration
- Explicit ownership check on every detail/edit/delete view:

```python
# In kyc/views.py
if not request.user.is_reviewer and application.owner != request.user:
    audit_logger.warning(f"IDOR ATTEMPT: User {request.user.username} tried ...")
    return HttpResponseForbidden(...)
```

### Step 3 — Detailed Audit Logging
Dual-channel logging: Python file logger + database `AuditLog` model.

```python
# settings.py — file-based logging config
LOGGING = {
    'handlers': {
        'audit_file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
        },
    },
    'loggers': {
        'kyc.audit': { 'handlers': ['audit_file', 'console'], 'level': 'INFO' },
    }
}

# kyc/views.py — every sensitive action is logged
audit_logger.info(
    f"User={request.user.username} | Action=view | "
    f"Target=KYCApplication:{public_id} | IP={ip}"
)
```

### Step 4 — Active Defense with `django-axes`
```python
# settings.py
INSTALLED_APPS = [..., 'axes']
MIDDLEWARE = [..., 'axes.middleware.AxesMiddleware']
AXES_FAILURE_LIMIT = 3          # Lock after 3 failed attempts
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_LOCKOUT_TEMPLATE = 'registration/lockout.html'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

---

## 👥 Team Role Coverage

### 1. Lead Cloud & DevOps Engineer
- **Render/Railway**: `Procfile`, `build.sh` — gunicorn with `$PORT`
- **Cloudinary**: `settings.py` — `CLOUDINARY_STORAGE` config, env-based toggle
- **Static files**: WhiteNoise middleware for production serving
- **Env vars**: All secrets in `.env`, `.env.example` template, `.gitignore`

### 2. API & IAM Engineer
- **DRF REST API**: `api/views.py` — ApplicationListAPI, ApplicationDetailAPI, StatsAPI
- **JWT Auth**: `SimpleJWT` — `/api/token/`, `/api/token/refresh/`
- **Field-level masking**: `masked_email` on `CustomUser`, `masked_document_number` on `KYCDocument`
- **RBAC permissions**: `IsReviewer`, `IsOwnerOrReviewer` DRF permission classes

### 3. Database Architect & RBAC Lead
- **Data models**: `CustomUser`, `KYCApplication`, `KYCDocument`, `AuditLog`
- **UUID public IDs**: Anti-IDOR — `public_id = UUIDField(default=uuid4, editable=False)`
- **Ownership filter**: `KYCApplication.objects.filter(owner=request.user)`
- **RBAC roles**: `applicant`, `reviewer`, `compliance`, `admin`
- **Immutable audit**: `AuditLogAdmin` disables `has_add_permission` & `has_change_permission`
- **Demo seeder**: `python manage.py seed_demo`

### 4. Frontend UI & Component Engineer
- **Dashboard interfaces**: `reviewer_dashboard.html` with stats grid, filters, paginated table
- **Applicant dashboard**: Progress bar, status timeline, document grid, onboarding flow
- **Interactive filters**: Status, risk, search filters with GET params
- **Custom template tags**: `kyc_tags.py` — `{% upload_form_fields %}`, `{{ status|status_icon }}`, `{{ risk|risk_color }}`
- **Formsets**: Inline document upload modal with drag & drop
- **Design system**: Dark enterprise theme — `static/css/main.css`, `static/js/main.js`

### 5. DevSecOps & Compliance Analyst
- **django-axes**: Brute-force protection, lockout after 3 attempts, custom lockout template
- **Python audit logging**: File-based `audit.log` + `security.log` via `LOGGING` config
- **Dual audit trail**: DB `AuditLog` model + file logger on every sensitive action
- **Security headers**: `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` (production)
- **IDOR logging**: Attempted unauthorized access logged as `WARNING` in `security.log`
- **Dependency manifest**: Pinned `requirements.txt` for SAST scanning

---

## 🌐 API Endpoints

| Method | URL                                | Auth     | Description                        |
|--------|------------------------------------|----------|------------------------------------|
| POST   | `/api/token/`                      | None     | Obtain JWT access + refresh tokens |
| POST   | `/api/token/refresh/`              | Refresh  | Rotate access token                |
| GET    | `/api/applications/`               | JWT      | List applications (RBAC-filtered)  |
| GET    | `/api/applications/<uuid>/`        | JWT      | Application detail (Anti-IDOR)     |
| GET    | `/api/applications/stats/`         | JWT+Rev  | Dashboard statistics               |
| GET    | `/api/audit-log/`                  | JWT+Comp | Full audit trail                   |
| GET    | `/api/me/`                         | JWT      | Current user info (masked email)   |

### Example JWT Usage
```bash
# 1. Obtain token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "kyc_reviewer", "password": "review123!"}'

# 2. Use token
curl http://localhost:8000/api/applications/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ☁️ Deployment (Render)

1. Push to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Set **Build Command**: `./build.sh`
4. Set **Start Command**: `gunicorn kyc_portal.wsgi:application --bind 0.0.0.0:$PORT`
5. Add Environment Variables:
   - `SECRET_KEY` — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.onrender.com`
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`

---

## 🔬 Security Testing

### Test Anti-IDOR
1. Login as `lisa_tan`
2. Get `juan_dela_cruz`'s application UUID from admin panel
3. Navigate to `/application/<juan_uuid>/`
4. → Returns **403 Forbidden**, logs **IDOR ATTEMPT** warning

### Test django-axes Lockout
1. Go to `/accounts/login/`
2. Enter wrong password **3 times** for the same username
3. → Account locked, redirected to lockout page
4. Check `logs/security.log` for the warning entries
5. Unlock via Django admin → Axes → Access Attempts → Delete

### Test Audit Logging
1. Login as `kyc_reviewer`
2. View any application
3. Check `logs/audit.log` — entry logged with username, action, IP, timestamp

---

## 📝 Notes

- **SQLite** is used by default for local dev; switch to PostgreSQL for production via `DATABASE_URL`
- **File uploads** store locally in `media/`; configure Cloudinary env vars to use cloud storage
- Log files are written to `logs/audit.log` and `logs/security.log` — ensure the `logs/` directory exists
- Run `python manage.py migrate` after any model changes
