# E-commerce Sales Insights Platform (Django Enterprise SaaS)

An enterprise-ready SaaS analytics platform built on Django, Pandas, and Plotly, converting the simple static analysis scripts into a responsive, multi-user business intelligence tool.

---

## Key Features

1. **Dashboard & KPIs**: Real-time business insights (Total Revenue, Orders, AOV, region metrics, cancellation/return rates, returning customers metrics, etc.).
2. **Interactive Visualizations**: Dynamic charts powered by Plotly (Monthly Sales, Revenue by Category, Region Breakdown, Daily Trends, Payment Channels, Order Status, and Revenue Heatmap).
3. **Advanced Filtering Console**: Dynamically filter charts, KPI cards, and lists by date range, payment types, categories, region, order status, and revenue ranges without page reloads (powered by HTMX/AJAX).
4. **Dataset Management**: Multi-dataset tracking. Upload CSV files, view audit history, preview rows, automatically clean column schemas, detect anomalies (missing values, duplicates), and toggle workspaces.
5. **PDF & Excel Reporting**: Generate executive PDF reports (using ReportLab) and styled multi-sheet Excel workbooks (using OpenPyXL) dynamically.
6. **SaaS User Authentication**: Multi-role support (Admin, Analyst, Viewer) with secure signup, login, profile configurations, and custom 6-digit unique random User IDs.
7. **AI-Powered Forecasting**: Linear regression modeling of historical order flows to project future monthly revenue.
816. **REST API endpoints**: Complete JSON integrations for dashboard metrics (`/api/kpis/`, `/api/charts/`, `/api/orders/`, `/api/forecast/`, `/api/reports/`).
17. **Production-Ready Deployment**: Configured for Render and Railway, PostgreSQL support via `.env`, and custom HTML Admin Panel (No Docker dependencies required).
18. **AI-Free Insight Generator**: Rule-based executive insights generating English sentences from KPI and anomaly detection data.

---

## Project Structure

```
E-commerce Sales Insights/
├── ecommerce_insights/
│   ├── settings/           # Modular Django Settings (base.py, __init__.py)
│   ├── urls.py             # Root routing (Admin, Dashboard, Users, Datasets)
│   ├── wsgi.py
│   └── asgi.py
├── dashboard/              # Core SaaS View Controller
│   ├── templates/          # Namespaced templates (dashboard/index.html, partials/)
│   ├── api_views.py        # Django REST Framework API endpoints
│   └── urls.py
├── users/                  # Access Control and Profile Configurations
│   ├── templates/          # Auth templates (registration/login.html, users/profile.html)
│   ├── models.py           # CustomUser model (Role-based access, 6-digit random User IDs)
│   └── forms.py
├── datasets/               # Upload management and schema validation
│   ├── templates/          # List, upload, preview, and confirmation templates
│   ├── models.py           # Dataset metadata and active state model
│   └── views.py            # Automatic CSV cleaning and pandas audit workflow
├── analytics/              # Reusable data analytics engines
│   ├── data_loader.py      # Pandas loading with Redis/Django database caching
│   ├── cleaning_engine.py  # Standardizing column headers and casting data types
│   ├── analytics_engine.py # Calculating KPIs and ML regressions
│   ├── chart_engine.py     # Plotly interactive figure constructor
│   ├── insight_engine.py   # AI-Free Rule-Based Insight Generator
│   ├── export_engine.py    # PDF and Excel builder packages
│   └── tests.py            # Analytics Unit Tests
├── templates/              # Global layout components (base.html, navbar, footer)
├── static/                 # Isolated Styles and Javascripts by app
│   ├── css/                # (global.css, dashboard.css, datasets.css, users.css)
│   └── js/                 # (core.js, dashboard.js)
├── media/                  # Datasets and uploaded materials storage
├── manage.py
├── requirements.txt        # Enterprise requirements list
└── setup_project.py        # Database migrations and superuser automated seeder
```

---

## Setup & Running Guide

### 1. Requirements Installation
Ensure Python 3.12+ is installed, then build and activate virtual environment:
```bash
python -m venv venv
# Windows (PowerShell)
.\venv\Scripts\activate
# Mac / Linux
source venv/bin/activate
```
Install dependencies:
```bash
pip install -r requirements.txt
```

On Windows PowerShell, you can run the project setup script instead:
```powershell
.\setup.ps1
```
This creates or reuses `venv`, installs pinned dependencies, and applies database migrations.

### 2. Auto-Migrate & Seed Demo Data
Use the automated seeder script. It will run migrations, create an administrator user, generate the synthetic transactions database, register, and activate the demo workspace:
```bash
python manage.py makemigrations users datasets
python manage.py migrate
python setup_project.py
```
*Note*: The seeder configures the default superuser credentials:
- **Username**: `admin`
- **Password**: `adminpassword`
- **Email**: `admin@example.com`

### 3. Running Server
Launch the Django server:
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` and sign in with the admin credentials above.

---

## Ollama AI Sales Insights

The dashboard includes an optional AI-powered insight card that sends the current filtered KPI snapshot to Ollama using Phi-3 Mini.

Start Ollama and download the model:
```bash
ollama serve
ollama pull phi3:mini
```

Apply the AI insight database migration and run Django:
```bash
python manage.py migrate
python manage.py runserver
```

Admins and Analysts can generate new insights from the dashboard. Viewers can open `/ai/history/` to view saved insight previews.

Optional `.env` overrides:
```ini
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3:mini
OLLAMA_TIMEOUT=60
```

---

## Production Deployment (Render / Railway)

This project is configured to be deployed using standard Python WSGI environments without Docker.

### 1. Environment Variables
Create a `.env` file in the root directory (or in your hosting platform dashboard) with the following:
```ini
DEBUG=False
SECRET_KEY=your_secure_secret_key_here
ALLOWED_HOSTS=your-app.onrender.com,your-app.up.railway.app
DATABASE_URL=postgres://user:password@hostname:port/dbname
```

### 2. Procfile (Optional for some hosts)
Create a `Procfile` in the root directory if your host requires it:
```
web: gunicorn ecommerce_insights.wsgi:application
```
*(You will need to run `pip install gunicorn psycopg2-binary` on your production server)*

### 3. Static Files
The application uses `WhiteNoise` (built-in to modern Django configs) to serve static files. Run collectstatic during your deployment build step:
```bash
python manage.py collectstatic --noinput
python manage.py migrate
```

---

## REST API Documentation

| Endpoint | Method | Authentication | Description |
|---|---|---|---|
| `/api/kpis/` | `GET` | Token/Session | Computes total sales, orders, AOV, cancellations and returns |
| `/api/charts/` | `GET` | Token/Session | Outputs Plotly configurations in JSON format |
| `/api/orders/` | `GET` | Token/Session | Fetches filtered order logs (limited to 50 rows) |
| `/api/forecast/` | `GET` | Token/Session | Computes linear regressions and predicts sales trends |
| `/api/reports/` | `GET` | Token/Session | Returns full report including KPIs and AI-Free Insights |
