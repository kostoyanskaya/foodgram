# Project: Foodgram
"Foodgram" is a website where users can publish their recipes, add other people's recipes to favorites, and subscribe to other authors' publications. Registered users also have access to the "Shopping List" service, which allows creating a list of products needed to prepare selected dishes. "Foodgram" creates a convenient space for sharing recipes and planning purchases, making the cooking process more structured and enjoyable.

[![Main Foodgram Workflow](https://github.com/kostoyanskaya/foodgram/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/kostoyanskaya/foodgram/actions/workflows/main.yml)

### Main features:
- Users can publish their recipes.
- Ability to add other people's recipes to favorites.
- Subscribe to other authors' publications.
- "Shopping List" service for creating a list of necessary products.
- Automatic redirection to the login page after registration.
- Ability to get a unique short link to a recipe.
- Logged-in users can add recipes to favorites and the shopping list.
- Users can download their shopping list in .txt format.
- Editing published recipes for their authors.


### The project mainly uses the following technologies and libraries:

- Django - the main framework for web application development.
- Django REST Framework - for building the API.
- Djoser - for managing user authentication and registration.
- Pillow - a library for image processing.
- PostgreSQL - as the database.
- Gunicorn - WSGI HTTP server for running the application.

## Installing the project on a remote server:

1. Log in to the remote server.

2. Run the commands on the server to install Docker and Docker Compose for Linux

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```

3. Create the foodgram folder

```
sudo mkdir foodgram
```

4. Navigate to the foodgram directory

```
cd foodgram/
```

5. You need to create a docker-compose.production.yml file and copy the contents of the project's docker-compose.production.yml

```
sudo touch docker-compose.production.yml
sudo nano docker-compose.production.yml
```

6. You need to create a .env file

```
sudo touch .env
sudo nano .env
```
7. Fill it out according to the example

```
POSTGRES_DB=example
POSTGRES_USER=example_user
POSTGRES_PASSWORD=example_password
DB_NAME=example
DB_HOST=db
DB_PORT=5432
```

8. Add the site domain to the Nginx configuration file, check the configuration, and reload it.
```
sudo nano /etc/nginx/sites-enabled/default
sudo nginx -t
sudo service nginx reload
```

9. Run the commands:

```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/backend_static/static/. /backend_static/static/
```
10. Load ingredients from csv:

```
docker exec -it <container_name> bash
python manage.py import_ingredients
python manage.py import_tags
```
Load ingredients from json:
```

python manage.py data_import_ingredients
python manage.py data_import_tags
```

## Author
#### [_Viktoriia_](https://github.com/kostoyanskaya/)
