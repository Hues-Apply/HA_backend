# Hues Apply Backend (HA_backend)

This is the official backend repository for the Hues Apply project. It is built using **Django** and  **Django REST Framework** , following industry best practices for scalable, modular, and maintainable APIs.

---

## 🚀 Tech Stack

* Python 3.10+
* Django 4.x
* Django REST Framework
* PostgreSQL
* Redis (optional for caching)
* Docker (for deployment and local dev containers)

---

## 📁 Folder Structure

```bash
HA_backend/
├── config/              # Project settings, URLs, WSGI/ASGI entry points
├── core/                # Shared logic/utilities
├── users/               # User authentication, profiles, roles
├── applications/        # Applications submitted by users
├── payments/            # Payment logic (if applicable)
├── templates/           # Email or HTML templates
├── static/              # Static files (JS, CSS, etc.)
├── media/               # Uploaded media files
├── manage.py
├── .env                 # Environment variables (not committed)
└── requirements.txt     # Python dependencies
```

---

## 🧱 Naming Conventions

* **Apps:** lowercase (`users`, `applications`)
* **Models:** PascalCase (`class UserProfile`)
* **Variables/Functions:** snake_case
* **Files:** snake_case.py

---

## ✅ Development Workflow

1. **Pull before you push:** Always pull from `main` before creating your branch.
2. **Create feature branches:**
   ```bash
   git checkout -b feat/<FeatureName>
   # or
   git checkout -b bugfix/<BugName>
   ```
3. **Never commit secrets** or `.env` files.
4. **Do not change core dependencies** unless agreed with the team.
5. **Use** `.env` for all sensitive configurations.

---

## ⚙️ Running Locally

```bash
# Clone the repo
$ git clone https://github.com/HuesApply/HA_backend.git

# Create virtualenv
$ python -m venv venv
$ source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
$ pip install -r requirements.txt

# Create .env file and configure DB, secret keys

# Apply migrations
$ python manage.py migrate

# Run server
$ python manage.py runserver
```

---

## 🧪 Testing

```bash
python manage.py test
```

---

## 🧼 Linting & Code Quality

Use `flake8`, `black`, or `pylint` to maintain code quality.

---

## 🔐 Security & Secrets

* Use `.env` for all secrets
* NEVER commit credentials or access tokens
* Follow Django security best practices

---

## 🌐 API Integration

This backend is responsible for serving RESTful API endpoints consumed by the [HA_frontend](https://github.com/Hues-Apply/HA_frontend) project. Ensure that:

* All endpoints follow REST conventions.
* Responses are standardized (preferably JSON).
* Proper status codes and error messages are returned.
* CORS is properly configured for frontend consumption.
* API documentation is kept up to date using tools like `drf-yasg` or `drf-spectacular`.

---

## 🔄 Revisions

This document will be updated as team needs and project requirements evolve.

---

## 📣 Communication

* Report blockers or issues early
* Push WIP (Work In Progress) branches if stuck
* **Don't push directly to** `main`

---

## 🤝 Contributors

* All contributors must follow branch naming, commit practices, and review guidelines.
* Forking is not allowed for internal devs. Always clone and pull from `main`.

Let's build something excellent.
