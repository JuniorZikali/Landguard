# LandGuard

A Web-Based Land Transaction Fraud Detection System for Zimbabwe.

**Final Year Project** — HIT 0400 Prototype, Harare Institute of Technology.

## What this system does

LandGuard helps protect Zimbabweans from land fraud by providing three core
services:

1. **Centralised Property Registry** — verified property records with full
   ownership and transaction history.
2. **Title Deed Authenticity Checker** — validates deed numbers and detects
   mismatched details against the registry.
3. **Buyer Fraud Risk Reports** — on-demand risk reports combining deed
   authenticity, ownership verification, double-listing detection,
   price-anomaly analysis, and land-baron pattern recognition.

## Quick start

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- pip and venv

### 1. Set up MySQL

Open MySQL as root and run:

```sql
CREATE DATABASE landguard_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'landguard_user'@'localhost' IDENTIFIED BY 'choose_a_strong_password';
GRANT ALL PRIVILEGES ON landguard_db.* TO 'landguard_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Install Python dependencies

```bash
cd landguard
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

If `mysqlclient` fails to install, on Ubuntu you may need:
```bash
sudo apt install pkg-config libmysqlclient-dev python3-dev build-essential
```
On Windows, install MySQL Connector/C from MySQL's website first.

### 3. Configure environment

```bash
cp .env.example .env
# Then edit .env and set DB_PASSWORD to the password you chose above.
```

### 4. Run migrations and create a superuser

```bash
python manage.py migrate
python manage.py createsuperuser     # for the admin panel
```

### 5. Seed demo data (optional but recommended)

```bash
python manage.py seed_demo_data
```

This creates 6 demo users, 12 Harare properties, and several transactions
including fraud scenarios you can demonstrate in your defence.

### 6. Run the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**.

## Demo accounts

After running `seed_demo_data`, the following accounts exist (password is
**TestPass123!** for all):

| Role | Email | What to demonstrate |
|---|---|---|
| Registrar | `registrar@landguard.zw` | Adding properties, viewing system overview |
| Seller (clean) | `chamu@example.com` | Normal listing flow |
| Seller (clean) | `rumbi@example.com` | Normal listing flow |
| Land Baron | `baron@example.com` | Multiple-listings flag |
| Impersonator | `impersonator@example.com` | Seller-mismatch flag |
| Buyer | `buyer@example.com` | Risk reports, deed checker |

## Project structure

```
landguard/
├── manage.py
├── requirements.txt
├── .env.example
├── landguard/              # Django project config
│   ├── settings.py         # Configured for MySQL + email login
│   ├── urls.py
│   └── wsgi.py
├── accounts/               # Users, profiles, auth, audit log
│   ├── models.py           # Profile, AuditLog
│   ├── backends.py         # EmailBackend (login by email)
│   ├── forms.py            # SignUpForm with national ID
│   └── views.py
├── properties/             # OBJECTIVE 1: Property registry
│   ├── models.py           # Property
│   ├── views.py            # list/detail/add/edit
│   └── management/commands/seed_demo_data.py
├── transactions/           # Fraud detection engine
│   ├── models.py           # Transaction, RiskFlag
│   └── risk_engine.py      # *** rule-based engine (8 rules) ***
├── verification/           # OBJECTIVE 2 + 3
│   ├── models.py           # VerificationRequest, FraudReport
│   ├── deed_checker.py     # *** title deed checker ***
│   └── report_generator.py # *** buyer risk report ***
├── dashboard/              # Role-aware home pages
├── templates/
│   ├── base.html           # Bootstrap 5 layout
│   ├── home.html
│   ├── accounts/
│   ├── properties/
│   ├── transactions/
│   ├── verification/
│   └── dashboard/
└── static/css/custom.css
```

## How the fraud detection works

The risk engine (`transactions/risk_engine.py`) evaluates each transaction
against **8 rules**:

| # | Rule | Severity | What it catches |
|---|---|---|---|
| 1 | Seller-ID mismatch | HIGH | Impersonation — seller ≠ registered owner |
| 2 | Duplicate active listing | HIGH | Double-selling |
| 3 | Recently transferred | HIGH | Selling property already sold |
| 4 | Price below market | MEDIUM | Suspicious pricing pressure |
| 5 | Disputed status | HIGH | Selling contested property |
| 6 | Multiple listings same seller | MEDIUM | Land-baron pattern |
| 7 | Incomplete property record | LOW | Reduced verification confidence |
| 8 | Unverified owner | LOW | Identity not yet confirmed |

Each rule produces a flag with severity (LOW=10, MEDIUM=25, HIGH=40 points).
The total is capped at 100 and mapped to LOW (<20), MEDIUM (20–49), HIGH (≥50).

The deed checker (`verification/deed_checker.py`) runs:
- Format validation (regex against Zimbabwe deed patterns)
- Registry lookup
- Cross-field validation (claimed ID, address)
- Status check (disputed/flagged/transferred)

The report generator (`verification/report_generator.py`) combines both
engines into a unified buyer-friendly report.

## Key URLs

- `/` — Home page (public)
- `/verification/deed-check/` — Public deed checker (Objective 2)
- `/verification/buyer-report/` — Buyer fraud report (Objective 3, login required)
- `/properties/` — Browse the registry (Objective 1)
- `/dashboard/` — Role-based dashboard (login required)
- `/admin/` — Django admin (superuser/staff only)

## Testing the prototype

After seeding, try these scenarios:

1. **Visit the home page** — landing page introduces the three features.
2. **Try `/verification/deed-check/`** — enter `1234/2020` (or any deed
   number from `/properties/`) and watch the authenticity report.
3. **Sign up as a new buyer** at `/accounts/signup/`.
4. **Generate a buyer report** at `/verification/buyer-report/` for any
   property — try a high-risk one to see flags in action.
5. **Log in as `baron@example.com`** to see the seller dashboard.
6. **Log in as `registrar@landguard.zw`** to see system-wide statistics.

## Default time zone

`Africa/Harare`. Edit `landguard/settings.py` to change.

## License

Academic project — not for commercial use.
