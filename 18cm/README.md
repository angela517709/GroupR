# 18cm Flask Application

## Overview
The 18cm application is a Flask-based web application designed to demonstrate basic functionality and structure of a Flask app.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd 18cm
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the application:
   - Update the `config.py` file with your specific settings.

4. Run the application:
   ```
   flask run
   ```

## Usage
- Navigate to `http://127.0.0.1:5000` in your web browser to access the application.

## File Structure
- `app/__init__.py`: Initializes the Flask application.
- `app/routes.py`: Defines the application routes.
- `app/models.py`: Contains data models.
- `app/templates/base.html`: Base HTML template.
- `app/templates/index.html`: Home page template.
- `config.py`: Configuration settings for the application.
- `requirements.txt`: Lists project dependencies.

## License
This project is licensed under the MIT License.