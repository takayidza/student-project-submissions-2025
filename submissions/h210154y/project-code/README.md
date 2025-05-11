# Trazo 

The application's admin dashboard was developed using Laravel and uses a model wrapped with FastAPI to classify documents. If you get stuck, you can consult the official Laravel documentation.

## Getting started

To get started, you need to set up the environment variables inside the admin folder to get the application running. The following are the extra env variables to set:

```sh
AI_API_URL=<link_to_model_api_running_instance>
AI_SERVICE_TOKEN=<token_to_access_model_api> 
```

Navigate into admin folder and install the neccessary dependencies:

### 1. 
```sh
composer install & npm install 
```

### 2. 

Run the database migrations:

```sh
php artisan migrate --seed 
```

### 3.

Makesure the model service api is running in separate terminal session before starting the application.

To run the app:

```sh
composer run dev
```

## Learn more

To learn more about the technologies used in this capstone project, see the following resources:

- [Laravel](https://laravel.com/docs/12.x) - the official Laravel documentation
- [Inertia](https://inertiajs.com/) - the official Inertia documentation
- [PDF Document Layout Analysis](https://github.com/huridocs/pdf-document-layout-analysis) - the official repository for huridocs pdf-document-layout-analysis used in this project.
