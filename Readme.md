# Project1 

## Technologies Stack
- Flask for building the backend API.
- Vue.js for creating dynamic user interfaces.
- SQLite for database management.
- Redis for caching data that is frequently accessed.
- Redis and Celery for executing batch processes.
- Bootstrap and CSS for crafting a responsive and good UI.

## Running Tests Locally
Before running this project locally, ensure you have the following installed:
- Python 
- SQLite 
- Redis server
- Celery 


## Installation
1.Install dependencies

```
pip install -r requirements.txt
```

2.Start the Flask backend:

```
python app.py
```
3.Access the application in your browser at `http://127.0.0.1:5000/`.

4.Start Redis server:

```
redis-server
```

5.Start the Celery worker & beat:

```
celery -A app.celery beat --loglevel=info
celery -A app.celery worker -l info
```

6.Start Mailhog

```
mailhog
```

7.Accessing Mailhog
```
ifconfig
```
Copy the inet value and use it as the host. Then, open your browser and navigate to http://inet_value:8025/




