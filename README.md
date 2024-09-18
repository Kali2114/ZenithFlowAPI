# ZenithFlow
ZenithFlow is a meditation and self-development platform designed to help users achieve mindfulness and personal growth. Built with modern technologies such as Django, REST API, Celery, Redis, and integrated with AWS, the application provides a seamless and scalable experience for hosting meditation sessions, tracking progress, and managing user subscriptions.

## Table of Contents
- [Features](#features)
- [Technologies](#technologies)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)


## Features
- User Registration & Authentication: Users can sign up, log in, and manage their profiles, including uploading avatars.
- Meditation Sessions: Hosts (instructors) can create meditation sessions, mark them as completed, and participants can rate sessions after completion.
- User Profiles: Each user has a profile with a customizable avatar, bio, total sessions attended, and time spent in meditation.
- Session Ratings: Participants can rate meditation sessions, and ratings are only allowed for completed sessions.
- Payment System: Only users with active subscriptions (via payments) can register for sessions.
- AWS Integration: The app is deployed on AWS using services like EC2, RDS, S3, and ElastiCache for scalability.
- Asynchronous Tasks: Celery with Redis is used to send notifications and handle background tasks.
- Automated CI/CD: The project uses GitHub Actions for CI/CD and CodeDeploy to automate deployments.

## Technologies
The following technologies and tools are used in ZenithFlow:

- Backend: Django, Django REST Framework
- Task Queue: Celery, Redis
- Database: PostgreSQL (via AWS RDS)
- Storage: AWS S3 for media files (avatars)
- Deployment: Docker, Docker Compose, GitHub Actions, AWS EC2, AWS CodeDeploy
- API Testing: Pytest, Django Test Framework

## Installation
To run ZenithFlow locally:

1. Clone the repository:

```
git clone https://github.com/your-repository/zenithflow.git
cd zenithflow
```

2. Install dependencies:

```
pip install -r requirements.txt
```

3. Set up the environment variables in a .env file with your AWS and database credentials:

```
DB_HOST=your-db-host
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASS=your-db-pass
REDIS_HOST=your-redis-host
REDIS_PORT=6379
```

4. Run the Docker containers:

```
docker-compose up --build
```

5. Run migrations:

```
docker-compose run app sh -c "python manage.py migrate"
```

6. Start the application:

```
docker-compose up
```

## Usage
Once the app is running, you can access the API at http://localhost:8000.

## API Endpoints

### User Authentication:

* POST /api/user/create/ - Register a new user
* POST /api/user/token/ - Obtain authentication token
* GET /api/user/me/ - Manage current authenticated user

### User Profiles:

* GET /user/<int:pk>/profile/ - View and edit the user's profile
* PATCH /user/<int:pk>/profile/upload-avatar/ - Upload a profile avatar

### Meditation Sessions:

* POST /sessions/ - Create a new session (instructor only)
* GET /sessions/ - List all sessions
* PATCH /sessions/<int:pk>/complete-session/ - Mark a session as completed
* POST /sessions/<int:pk>/add-technique/ - Add a technique to a session

### Ratings:

* POST /sessions/<int:session_id>/ratings/ - Rate a session
* GET /sessions/<int:session_id>/ratings/ - Get session ratings

## Testing
ZenithFlow follows Test-Driven Development (TDD), with over 100 tests to ensure functionality. To run tests, use the following command:

```
docker-compose run --rm app sh -c "python manage.py test"
```

## Contributing
Contributions are welcome! If you'd like to contribute:

- Fork the repository
- Create a new branch (git checkout -b feature-branch)
- Commit your changes (git commit -m 'Add feature')
- Push the branch (git push origin feature-branch)
- Open a Pull Request

Please make sure your code adheres to the project’s coding standards and passes all tests.

## License
This project is licensed under the GPL-3.0 License. See the LICENSE file for more details.