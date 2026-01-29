# Web Application Monitor

[![Python 3.10 | 3.11](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)](https://www.python.org/)
[![Lint (pylint)](https://github.com/chervaliery/watcher/actions/workflows/lint.yml/badge.svg)](https://github.com/chervaliery/watcher/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/chervaliery/watcher/branch/main/graph/badge.svg)](https://codecov.io/gh/chervaliery/watcher)
[![CodeQL](https://github.com/chervaliery/watcher/actions/workflows/codeql.yml/badge.svg)](https://github.com/chervaliery/watcher/actions/workflows/codeql.yml)

Monitor personal web applications (different hostnames, optional client certificates) with regular HTTP health checks and a dashboard.

- **Backend**: Django + MariaDB
- **Frontend**: AngularJS 1.8.2
- **Scheduling**: Cron + management command `run_checks`

## Setup

### 1. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database

**Development (default):** SQLite is used automatically. No setup needed; a `db.sqlite3` file is created in the project root after `migrate`.

**Production with MariaDB:** Set `USE_MARIADB=1` and create a database and user:

```sql
CREATE DATABASE watcher CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'watcher'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL ON watcher.* TO 'watcher'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Environment variables

Configure via environment (or leave defaults for local dev):

| Variable              | Description                                                    | Default                          |
| --------------------- | -------------------------------------------------------------- | -------------------------------- |
| `USE_MARIADB`         | Set to a non-empty value to use MariaDB instead of SQLite      | (unset → SQLite)                 |
| `MARIADB_NAME`        | Database name (when `USE_MARIADB` is set)                      | `watcher`                        |
| `MARIADB_USER`        | Database user                                                  | `watcher`                        |
| `MARIADB_PASSWORD`    | Database password                                              | `watcher`                        |
| `MARIADB_HOST`        | Database host                                                  | `localhost`                      |
| `MARIADB_PORT`        | Database port                                                  | `3306`                           |
| `DJANGO_SECRET_KEY`   | Django secret                                                  | (dev default; set in production) |
| `DJANGO_DEBUG`        | Debug mode                                                     | `1`                              |
| `DJANGO_ALLOWED_HOSTS`| Comma-separated hosts                                          | `localhost,127.0.0.1`            |
| `CORS_ALLOWED_ORIGINS`| Allowed CORS origins                                           | `http://localhost:8000`          |
| `ALERT_THRESHOLD`     | Consecutive failures/successes before sending an email         | `5`                              |
| `MAILJET_API_KEY`     | Mailjet API key (optional; if unset, no alert emails)          | (unset)                          |
| `MAILJET_SECRET`      | Mailjet API secret                                             | (unset)                          |
| `MAILJET_FROM_EMAIL`  | Sender email for alerts                                        | (unset)                          |
| `MAILJET_ALERT_TO`    | Comma-separated recipient email(s) for alerts                  | (unset)                          |

Example (SQLite, dev):

```bash
export DJANGO_SECRET_KEY=your-secret-key
```

Example (MariaDB, production):

```bash
export USE_MARIADB=1
export MARIADB_PASSWORD=your_password
export DJANGO_SECRET_KEY=your-secret-key
```

### 4. Migrations and run

```bash
python manage.py migrate
python manage.py createsuperuser   # optional, for Django admin
python manage.py runserver
```

- Dashboard: http://localhost:8000/dashboard/
- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## Regular health checks (cron)

Run health checks on a schedule so each watched application is checked at its configured interval.

**Option: cron**

Run the management command every 1–5 minutes. Each app is only checked if the last check was longer than its `check_interval_seconds` ago.

```bash
# Example: every 2 minutes
*/2 * * * * cd /path/to/watcher && .venv/bin/python manage.py run_checks
```

Use the full path to your project and venv in production.

## Email alerts (Mailjet)

After **N consecutive failures** (N = `ALERT_THRESHOLD`, default 5), a single **"app is down"** email is sent via Mailjet. After **N consecutive successes** following that, a single **"app is back up"** email is sent. Only one down and one up email per incident; the cycle repeats for the next incident.

**Configuration:** Set `MAILJET_API_KEY`, `MAILJET_SECRET`, `MAILJET_FROM_EMAIL`, and `MAILJET_ALERT_TO` (comma-separated recipients). If any of these are unset, no alert emails are sent (checks still run).

Example (production):

```bash
export ALERT_THRESHOLD=5
export MAILJET_API_KEY=your_api_key
export MAILJET_SECRET=your_secret
export MAILJET_FROM_EMAIL=alerts@yourdomain.com
export MAILJET_ALERT_TO=admin@yourdomain.com,ops@yourdomain.com
```

## Client certificates

For applications that require mutual TLS (client certificate), both **P12 (PKCS#12)** and **PEM (cert + key)** are supported.

1. **Store certs on the server** (e.g. `.p12` or PEM files). Do not store cert content in the database.
2. **Restrict file permissions** so only the app user can read them:
   ```bash
   chmod 600 /path/to/client.p12
   # or for PEM: chmod 600 /path/to/client.key && chmod 644 /path/to/client.pem
   ```
3. **Configure the watched application** (via dashboard “Manage applications” or API):
   - **P12**: **Client P12 path** (e.g. `/etc/watcher/certs/client.p12`) and **Client P12 password** (optional; leave blank if the P12 is unencrypted).
   - **PEM** (still supported via API): **Client cert path** and **Client key path**.
   - **CA bundle path** (optional): path to CA bundle for server verification (e.g. `/etc/ssl/certs/ca-certificates.crt`).

If **Client P12 path** is set, the checker uses the P12 file (with optional password). Otherwise, if both client cert path and client key path are set, the checker uses PEM. Leave all empty for applications that do not require a client certificate.

**Security**: Do not log cert paths or passwords in production. Keep `DJANGO_DEBUG=0` in production.

## API

- `GET /api/dashboard/` – Dashboard data (latest check per app, optional 24h stats).
- `GET /api/applications/` – List watched applications.
- `POST /api/applications/` – Create (JSON body: `name`, `base_url`, `hostname`, `check_interval_seconds`, `is_active`, `client_p12_path`, `client_p12_password`, `ca_bundle_path`; PEM `client_cert_path` / `client_key_path` still supported).
- `GET /api/applications/<id>/` – Detail.
- `PATCH /api/applications/<id>/` – Update (partial JSON).
- `DELETE /api/applications/<id>/` – Delete.
- `GET /api/applications/<id>/history/` – Paginated check history (`?page=1&page_size=20`).

## Production

- Set `DJANGO_DEBUG=0` and a strong `DJANGO_SECRET_KEY`.
- Run behind HTTPS (e.g. nginx or a reverse proxy).
- Restrict `CORS_ALLOWED_ORIGINS` to your front-end origin(s).
- Consider rate limiting on `/api/` (e.g. nginx or Django middleware).
