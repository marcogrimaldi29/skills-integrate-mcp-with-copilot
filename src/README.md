# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Persist activities and student registrations in SQLite

## Getting Started

1. From the repository root, install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application from the repository root:

   ```
   uvicorn src.app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student from an activity                                |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activities and participants are stored in `src/activities.sqlite`, which is
created automatically and is excluded from version control. On first startup,
the existing activities and their initial participants are seeded into the
database. Subsequent startups keep the persisted data instead of reseeding it.

To store the database elsewhere, set `ACTIVITIES_DB_PATH` to the desired file
path before starting the application. Back up this SQLite file to preserve
activity and registration data.
