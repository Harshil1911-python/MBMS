# CityLight Sindhi Samaj Surat — Marriage Bureau Management Software

A production-grade Flask web application for managing a community marriage bureau: candidate
biodata registration, admin verification workflow, member browsing/search, Kundli compatibility
screening, PDF biodata generation with QR codes, and full admin tooling (CSV import/export,
backups, SMTP settings, theming, activity logs).

---

## 1. Tech Stack

- **Backend:** Python 3.13, Flask 3, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF, Flask-Limiter
- **Frontend:** Bootstrap 5, Jinja2, vanilla JS, Chart.js
- **Database:** SQLite (local dev) / PostgreSQL (Render production)
- **PDF/QR/Imaging:** ReportLab, qrcode, Pillow
- **Data:** pandas, openpyxl (CSV/Excel import-export)
- **Security:** bcrypt password hashing, Fernet-encrypted SMTP credentials, CSRF protection, rate limiting

## 2. Project Structure

```
mbms/
├── app/
│   ├── models/          # SQLAlchemy models (User, Profile, Photo, Document, Activity, Settings)
│   ├── routes/           # Blueprints: auth, admin, member, profile, public
│   ├── services/         # Business logic: PDF gen, QR gen, Kundli matching, CSV, backups, settings
│   ├── forms/             # Flask-WTF forms
│   ├── utils/             # RBAC decorators, search/helpers
│   ├── templates/         # Jinja templates (admin/member/auth/profile/public/partials)
│   ├── static/             # css/js/uploads/qr/generated_pdf
│   ├── config.py
│   ├── extensions.py
│   ├── cli.py
│   └── __init__.py        # App factory
├── wsgi.py
├── requirements.txt
├── render.yaml
├── Procfile
├── runtime.txt
├── .env.example
└── README.md
```

## 3. User Roles

| Role | Capabilities |
|---|---|
| **Admin** | Full control: manage users/profiles, approve/reject, CSV import/export, backups, SMTP/theme settings, announcements, activity/login logs |
| **Member** | Browse & search approved profiles, download biodata PDFs, Kundli matching, favourites, compare, saved searches |
| **Groom / Bride** | Register & edit own biodata (photos/documents/kundli) until approved; profile becomes read-only after approval |

## 4. Local Setup

```bash
# 1. Clone and enter the project
cd mbms

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set SECRET_KEY, ENCRYPTION_KEY (see comment in file for how to generate one)

# 5. Initialize the database
export FLASK_APP=wsgi.py         # Windows (PowerShell): $env:FLASK_APP="wsgi.py"
flask init-db
flask seed-demo                   # creates default admin + settings
flask create-admin                # OR interactively create your own admin

# 6. Run the development server
flask run
# Visit http://127.0.0.1:5000
```

Default seeded admin (created only if no admin exists yet, via `flask seed-demo`):
```
Email:    admin@citylightsindhisamaj.org
Password: Admin@12345
```
**Change this password immediately after first login.**

## 5. Deployment on Render

### Option A — render.yaml Blueprint (recommended)
1. Push this project to a GitHub/GitLab repository.
2. In Render, choose **New > Blueprint** and point it at your repo. Render will read `render.yaml`
   and provision both the web service and a PostgreSQL database automatically.
3. Render auto-generates `SECRET_KEY` and `ENCRYPTION_KEY`. `DATABASE_URL` is wired automatically
   from the provisioned database.
4. On first deploy, the start command runs `flask init-db && flask seed-demo` before starting
   Gunicorn — this creates all tables and the default admin account.
5. Log in with the seeded admin credentials above and change the password immediately.

### Option B — Manual Web Service
1. Create a new **Web Service** on Render, connect your repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `flask init-db && flask seed-demo && gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 3`
4. Add a PostgreSQL database and set `DATABASE_URL` in environment variables (Render provides this
   automatically if you attach a Render Postgres instance).
5. Set `SECRET_KEY` and `ENCRYPTION_KEY` environment variables (long random strings).
6. Set `FLASK_APP=wsgi.py` and `FLASK_ENV=production`.

### Notes
- Uploaded photos/documents/QR codes/generated PDFs are stored on local disk under
  `app/static/uploads`, `app/static/qr`, `app/static/generated_pdf`. Render's filesystem is
  **ephemeral** on the free/starter plans — for persistent file storage in production, attach a
  [Render Disk](https://render.com/docs/disks) mounted at the app's `static/uploads` path, or
  migrate the upload services to an object store (S3-compatible) for a fully durable setup.
- The included `init-db` bootstrap uses `db.create_all()` for a reliable first deploy. For future
  schema changes, initialize Alembic-based migrations locally with `flask db init && flask db migrate`
  and switch the release command to `flask db upgrade`.

## 6. Key Features Implemented

- Full biodata registration form covering personal, career, location, contact, lifestyle,
  partner-preference, astrology, and medical sections, with photo (min 5/max 20) and document
  uploads (Aadhar, Passport, PAN, Driving License, Kundli).
- Role-based access control (Admin / Member / Groom-Bride) enforced via decorators.
- Admin approval workflow: pending → approved / rejected / suspended, with audit notes.
- Recycle bin (soft delete + restore + permanent delete) and duplicate-profile detection.
- Profile merge tool for admins.
- Advanced multi-field search & filtering (age, height, caste, education, income, manglik, etc.)
  with sorting and pagination.
- One-click professional biodata **PDF generation** (ReportLab) with embedded photo and QR code.
- **QR codes** linking to a public, read-only profile page.
- **Kundli Matching Engine** — simplified Ashtakoot Guna Milan (8-fold Vedic compatibility scoring)
  based on Rashi/Nakshatra, with dosha detection and recommendations.
- CSV/Excel import and export of profiles.
- ZIP database + asset backup/download from the admin panel.
- SMTP settings stored **encrypted** (Fernet) in the database — never hardcoded.
- Theme customization (primary/secondary/accent colors, optional dark mode toggle).
- Activity logs and login logs for security auditing.
- Announcements/homepage banner, success stories, FAQs, contact form.
- Favourites, recently-viewed, profile comparison, and saved searches for members.
- Rate limiting on login/registration/contact endpoints; bcrypt password hashing; CSRF protection
  on every state-changing form.

## 7. Scope Notes (Trimmed / Simplified for This Build)

Given the very large scope of the original specification, a few items were simplified or left as
straightforward extension points rather than fully built out, so the delivered system stays
genuinely functional end-to-end rather than including stubbed placeholders:

- **Kundli matching** uses Rashi/Nakshatra-based Ashtakoot scoring (the standard first-pass
  compatibility screen used by most matrimonial platforms). Full birth-chart/Dasha analysis needs
  precise ephemeris calculation and is outside this scope — the UI notes this and recommends
  consulting an astrologer for final confirmation.
- **Custom fields / dynamic form builder** for admins was not built; the schema instead covers the
  full fixed field set requested in the spec, which covers all listed data points.
- **CMS page editor** ships with a working `CMSPage`/`FAQ`/`Testimonial`/`Announcement` data model
  and public pages, but there's no rich WYSIWYG admin editor UI for CMS pages yet (content can be
  seeded/edited directly via the database or a quick admin form can be added following the existing
  `Announcement` CRUD pattern).
- **Email sending** — SMTP settings are fully implemented (encrypted storage, admin UI), but actual
  outbound email triggers (e.g. "profile approved" notification emails) are not wired up; the
  settings are ready for a `flask-mail`/`smtplib` integration to be added on top.
- File storage is local-disk based (see Render deployment notes above about persistence).

## 8. Security Checklist

- [x] bcrypt password hashing (12 rounds)
- [x] CSRF protection on all forms
- [x] Role-based route protection
- [x] Rate limiting on auth/contact endpoints
- [x] SMTP credentials encrypted at rest (Fernet)
- [x] Secure filename handling + extension allow-lists on all uploads
- [x] SQL injection protection via SQLAlchemy ORM (parameterized queries throughout)
- [x] Session cookies HTTPOnly + SameSite=Lax (Secure flag on in production)
- [x] Activity & login audit logs

---

Powered by SERENIA UPTIME · TECH SERENIA
