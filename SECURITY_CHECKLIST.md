# Security & Version Control Checklist

## ⚠️ CRITICAL ISSUES FOUND

### 1. **EXPOSED SECRET KEY** 🔴 HIGH PRIORITY
- **Location**: `config/settings.py` line 29
- **Current**: `SECRET_KEY = 'h%voaxg@x80+c8h@b#vp&2pgfv=ltq-4s%w0!3m!!vkcmrb&sy'`
- **Risk**: Hardcoded secret keys in public repos allow attackers to forge session tokens, JWTs, and bypass CSRF protection
- **Fix**: Move to `.env` file and load via `python-decouple` or `django-environ`

### 2. **db.sqlite3 IN REPO** 🟠 MEDIUM PRIORITY
- **Location**: Project root
- **Risk**: Database file with all data, users, and hashed passwords is public
- **Status**: Already in `.gitignore` ✅, but if accidentally committed before, need to purge from history

### 3. **Database file and Credentials**
- Ensure `.env` file is in `.gitignore` (already is ✅)
- Never commit actual `.env` files with real secrets

---

## ✅ What's Already Good

- `.gitignore` properly excludes `.env`, `db.sqlite3`, `__pycache__`, `.venv`
- `.gitignore` excludes `.vscode/` and IDE files
- No hardcoded API keys (Stripe, Twilio, AWS) detected ✅
- No plaintext passwords in code ✅

---

## 📋 Action Items (Before Making Public)

### Step 1: Fix SECRET_KEY (5 min)
Create `.env.example` template (already exists in `frontend/`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

Update `config/settings.py` to load from env:
```python
from decouple import config

SECRET_KEY = config('SECRET_KEY', default='change-me-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
```

Install: `pip install python-decouple` (add to requirements.txt)

### Step 2: Create `.env.example` Template
Copy your `.env` (if exists) to `.env.example`, replace real values with placeholders.

### Step 3: Clean Git History (if needed)
If you've already committed `db.sqlite3` or `.env` files with secrets:
```bash
git rm --cached db.sqlite3
git rm --cached .env
git commit -m "Remove sensitive files from history"
git push
```

**To purge from entire history** (⚠️ rewrites history):
```bash
pip install git-filter-repo
git filter-repo --path db.sqlite3 --invert-paths
git filter-repo --path .env --invert-paths
```

### Step 4: Document in README
Add a "Setup" section to `README.md`:
```markdown
## Setup (Development)

1. Clone the repo
2. Create `.env` from `.env.example`
3. Install dependencies: `pip install -r requirements.txt`
4. Run migrations: `python manage.py migrate`
5. Run server: `python manage.py runserver`
```

### Step 5: Add `.env.example` to Repo
Make sure it's committed (no secrets):
```bash
git add .env.example
git commit -m "Add .env template"
```

---

## 📦 Files to Check Before Public Release

| File/Folder | Status | Action |
|---|---|---|
| `.env` (actual) | ⚠️ NOT in repo (good!) | Keep out; add to `.gitignore` |
| `.env.example` | Missing in root | Create from your `.env`, remove secrets |
| `config/settings.py` | 🔴 **Has hardcoded SECRET_KEY** | Use `decouple` to load from env |
| `db.sqlite3` | ✅ Ignored | OK (auto-generated) |
| `Pipfile.lock` | ✅ Committed | OK (reproducibility) |
| `frontend/.env.example` | ✅ Exists | Good |
| `.gitignore` | ✅ Good | No changes needed |

---

## 🔒 Production Security Notes

### For `.exe` Bundling
- `.env` file is NOT bundled by default (good!)
- Create `config.ini` or `.env` in the same folder as `.exe` on deployment
- Example: `Restaurant.exe` lives in `dist/Restaurant/`, place `.env` next to it

### Sample Production `.env`
```env
SECRET_KEY=generate-a-strong-random-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
RESTAURANT_NAME=Your Restaurant
```

**Generate strong SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Final Checklist

- [ ] Replace hardcoded `SECRET_KEY` in `config/settings.py` with env-based loading
- [ ] Create `.env.example` in project root with placeholders
- [ ] Add `python-decouple` to `requirements.txt`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test that app runs with env variables
- [ ] Clean git history if secrets were committed (optional but recommended)
- [ ] Update `README.md` with setup instructions
- [ ] Add `.env.example` to git
- [ ] Final push to public repo

---

## One-Liner Fixes (Copy & Paste)

**Generate a new SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Install decouple:**
```bash
pip install python-decouple
```

---

You're ~95% ready! Just fix the SECRET_KEY and create `.env.example` before going public. 🚀
