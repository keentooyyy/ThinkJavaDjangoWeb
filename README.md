# ThinkJavaWeb

<div align="center">

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2.7-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)

</div>

## About

ThinkJavaWeb is a comprehensive web-based control panel for managing the [ThinkJava Unity Game](https://github.com/keentooyyy/ThinkJavaRewrite). This Django-powered Student Management System provides a complete administrative interface for tracking student progress, managing game content, and analyzing performance data from the Unity game.

### Key Features

- Multi-role authentication system (Admin, Teacher, Student)
- Real-time student progress tracking from Unity game
- Pre-test and Post-test management
- Student rankings and leaderboards
- Progress analytics and reporting
- Section-based academic organization
- Game level and achievement management

## Prerequisites

Before running the project, ensure you have the following installed:

- **[Docker Desktop](https://www.docker.com/get-started/)** (Includes both Docker Engine and Docker Compose)

You can verify installation with:

```bash
docker --version
docker compose version
```

## Environment Setup

### Step 1: Create Environment File

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
DB_NAME=thinkjava_db
DB_USER=thinkjava_user
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432

# Admin Account (Required for seed_admin command)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_FIRST_NAME=System
ADMIN_LAST_NAME=Admin

# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> **Note:** Replace all placeholder values with your own secure credentials.

## Installation and Deployment

### Step 2: Build Docker Image

Build the container using Docker Compose:

```bash
docker compose build
```

This step installs Python 3.12, PostgreSQL client libraries, project dependencies from `requirements.txt`, and sets up Gunicorn for production deployment.

### Step 3: Run Database Migrations

After the container is running, execute migrations:

```bash
docker compose exec web python manage.py migrate
```

This initializes the database schema for:
- Student Management System
- Game Progress tracking
- User authentication
- Pre/Post test system

### Step 4: Create Admin Account

Create a default admin user:

```bash
docker compose exec web python manage.py seed_admin
```

This creates an account using values from your `.env` file. If the account already exists, you'll see a message indicating it's already created.

You can update admin credentials by modifying your `.env` file and running the command again.

### Step 5: Seed Academic Data (Optional)

To populate the database with sample academic structure:

```bash
# Seed departments, year levels, and sections
docker compose exec web python manage.py seed_academic_data

# Seed game levels
docker compose exec web python manage.py seed_levels

# Seed achievements
docker compose exec web python manage.py seed_achievements

# Seed teachers (optional)
docker compose exec web python manage.py seed_teachers

# Seed students with progress (optional)
docker compose exec web python manage.py seed_students --students 20
```

> **Note:** These commands are optional and mainly for development/testing purposes.

## Running the Application

### Development Mode

Start the Django application in development mode:

```bash
docker compose up
```

This will:
- Start PostgreSQL database
- Run Django migrations automatically
- Start Django development server on port 8000

Access the application at: [http://localhost:8000](http://localhost:8000)

### Production Mode

To run with Nginx reverse proxy and SSL (Let's Encrypt):

```bash
docker compose --profile production up -d
```

This starts:
- **Web** (Django + Gunicorn)
- **Database** (PostgreSQL)
- **Nginx** (Reverse proxy)
- **Certbot** (SSL certificate management)

The application will be available at:
- HTTP: [http://localhost](http://localhost)
- HTTPS: [https://localhost](https://localhost) (if SSL configured)

## Configuration

### Changing Default Port

To change the port Django runs on, edit the following line in `docker-compose.yml`:

```yaml
ports:
  - "8000:8000"
```

The format is `HOST_PORT:CONTAINER_PORT`. To use port 9000, change it to:

```yaml
ports:
  - "9000:8000"
```

Then restart your container:

```bash
docker compose down
docker compose up --build
```

The application will now be available at: [http://localhost:9000](http://localhost:9000)

## Development Notes

- **Auto-migrations:** Migrations run automatically on container start
- **Hot reload:** Mounted volume (`.:/app`) enables instant code reloads during development
- **Container auto-restart:** Containers auto-restart if they crash (`restart: unless-stopped`)
- **Resource limits:** Containers have CPU and memory limits configured for efficient resource usage

## Management Commands

The project includes several management commands for data seeding and maintenance:

```bash
# Admin & Users
docker compose exec web python manage.py seed_admin

# Academic Structure
docker compose exec web python manage.py seed_academic_data
docker compose exec web python manage.py seed_teachers
docker compose exec web python manage.py seed_students --students 20

# Game Content
docker compose exec web python manage.py seed_levels
docker compose exec web python manage.py seed_achievements

# Progress Management
docker compose exec web python manage.py sync_progress
docker compose exec web python manage.py rank_students
docker compose exec web python manage.py reset_all_progress

# Level/Achievement Control
docker compose exec web python manage.py lock_level <level_name>
docker compose exec web python manage.py unlock_level <level_name>
docker compose exec web python manage.py lock_all_levels
docker compose exec web python manage.py unlock_all_levels
```

## Verification

After startup, verify the following endpoints:

- **Login Page:** [http://localhost:8000/](http://localhost:8000/)
- **Admin Dashboard:** [http://localhost:8000/admin/](http://localhost:8000/admin/) (if admin seeded)
- **Student Dashboard:** [http://localhost:8000/student/dashboard/](http://localhost:8000/student/dashboard/)
- **Teacher Dashboard:** [http://localhost:8000/teacher/dashboard/](http://localhost:8000/teacher/dashboard/)

If all pages load successfully, your local development environment is ready.

## Tech Stack

- **Backend:** Django 5.2.7 (Python 3.12)
- **Database:** PostgreSQL 16
- **Frontend:** Bootstrap 5 + Custom CSS/JS
- **Web Server:** Nginx (production)
- **WSGI Server:** Gunicorn (production)
- **SSL:** Certbot/Let's Encrypt (production)
- **Runtime:** Docker + Docker Compose
- **Additional Libraries:**
  - Pillow (image processing)
  - openpyxl (Excel export)
  - aiohttp (async HTTP)
  - psycopg2 (PostgreSQL adapter)

## Project Structure

```
ThinkJavaDjangoWeb/
├── StudentManagementSystem/    # Main Django app
│   ├── models/                  # Database models
│   ├── views/                   # View controllers
│   ├── templates/               # HTML templates
│   └── urls/                    # URL routing
├── GameProgress/                # Game progress tracking app
│   ├── models/                  # Level & achievement models
│   ├── views/                   # Progress API endpoints
│   └── management/commands/     # Management commands
├── ThinkJava/                   # Django project settings
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container definition
└── requirements.txt             # Python dependencies
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

```bash
# Check if database container is running
docker compose ps

# View database logs
docker compose logs db

# Restart all services
docker compose restart
```

### Port Already in Use

If port 8000 is already in use:

1. Change the port in `docker-compose.yml` (see "Changing Default Port" above)
2. Or stop the service using port 8000

## License

This project is for **personal use only**. Any commercial use is not the responsibility of the project maintainer. Users must ensure they have proper rights and licenses for all assets, libraries, and dependencies used in this project. The project maintainer assumes no liability for any misuse or unauthorized use of this software.
