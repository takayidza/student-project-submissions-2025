# Compliance Monitoring System - User Manual

## Table of Contents
1. [System Overview](#system-overview)
2. [Installation and Setup](#installation-and-setup)
3. [Running the System](#running-the-system)
4. [Using the Web Interface](#using-the-web-interface)
   - [Authentication](#authentication)
   - [Dashboard](#dashboard)
   - [Device Management](#device-management)
   - [Monitoring](#monitoring)
   - [Notifications](#notifications)
   - [Policies](#policies)
   - [Blocked Software Management](#blocked-software-management)
   - [Reports](#reports)
5. [Using the Telegram Bot](#using-the-telegram-bot)
6. [Command Line Interface (CLI) Commands](#command-line-interface-cli-commands)
7. [Additional Notes](#additional-notes)

---

## System Overview

The Compliance Monitoring System is a Django-based application designed to monitor devices within an organization for compliance with security policies. It includes features such as device registration, software scanning, compliance reporting, anomaly detection, and integration with a Telegram bot for remote management.

Key components:
- Web interface for administrators and users
- AI/ML models for compliance analysis and malware detection
- Telegram bot for authenticated remote commands
- Background task processing with Celery
- REST API endpoints for integration and automation

---

## Installation and Setup

### Requirements

The system requires Python and dependencies listed in `requirements.txt`. Key dependencies include Django, Celery, Django Channels, python-telegram-bot, scikit-learn, pandas, numpy, Redis, and others.

### Setup Steps

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Configure the database (default is SQLite).
5. Set environment variables, including `TELEGRAM_BOT_TOKEN` in `backend/settings.py` or environment.
6. Run migrations:
   ```
   python manage.py migrate
   ```
7. Create a superuser for admin access:
   ```
   python manage.py createsuperuser
   ```
8. Start Redis server (required for Celery and Channels).
9. Start Celery worker and beat scheduler for background tasks.
10. Run the Django development server:
    ```
    python manage.py runserver
    ```

---

## Running the System

### Web Interface

Access the web interface at `http://localhost:8000/` (or your configured host/port).

### Telegram Bot

Start the Telegram bot with:
```
python manage.py start_telegram_bot
```
The bot requires users to authenticate with their Django credentials and supports commands for scanning devices, checking status, listing devices and installed software, and logging out.

---

## Using the Web Interface

### Authentication

- Login with your Django username and password.
- Admin users have full access; regular users have restricted views based on ownership.

### Dashboard

- Overview of device compliance status.
- Statistics on device types, OS distribution, and recent notifications.

### Device Management

- List all devices (admin) or your own devices (user).
- Add, edit, or delete devices.
- View device details including installed software and activity reports.

### Monitoring

- Live monitoring dashboard showing real-time device status.
- Detailed monitoring for individual devices.
- Historical monitoring logs (admin only).

### Notifications

- View notifications related to compliance and security.
- Mark notifications as read.

### Policies

- Admins can create, update, and delete compliance policies.
- Define policy criteria for compliance checks.

### Blocked Software Management

- Admins can manage blocked software entries.
- Add, edit, delete, and toggle active status of blocked software.
- View installations of blocked software on devices.

### Reports

- Compliance reports showing non-compliant devices and blocked software.
- Device-specific compliance history and activity reports.

---

## Using the Telegram Bot

- Authenticate with `/start` by providing your Django username and password.
- Available commands after authentication:
  - `/scan` - Run compliance scan (admin only).
  - `/status` - Check your devices.
  - `/mydevices` - List your registered devices.
  - `/software` - List installed software on your devices.
  - `/logout` - End your session.

---

## Command Line Interface (CLI) Commands

Available Django management commands:

- `backup_data` - Backup system data.
- `cleanup_reports` - Cleanup old reports.
- `compliance_report` - Generate compliance reports.
- `retrain_model` - Retrain AI models.
- `scan_all_devices` - Scan all devices for compliance.
- `scan_compliance` - Run compliance scan.
- `scan_devices` - Scan devices.
- `send_command` - Send commands to devices.
- `start_telegram_bot` - Start the Telegram bot.
- `train_ai_models` - Train AI models.
- `train_model` - Train models.

Run commands with:
```
python manage.py <command_name>
```

---

## Additional Notes

- The system uses Celery with Redis for background task processing.
- AI models are stored in the `management/ai/models` directory.
- Logs are stored in the `logs/` directory.
- Backups are stored in the `backups/` directory.
- The system supports REST API endpoints for integration and automation.
- For detailed API usage, refer to the URL patterns in `management/urls.py`.

---

This manual provides an overview to help users and administrators effectively use the Compliance Monitoring System.
