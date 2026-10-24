"""SQLite-backed storage for activities and their participants."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator, Mapping, TypedDict


class ActivityData(TypedDict):
    description: str
    schedule: str
    max_participants: int
    participants: list[str]


class ActivityNotFoundError(Exception):
    """Raised when an operation references an unknown activity."""


class ParticipantAlreadySignedUpError(Exception):
    """Raised when a participant is already registered for an activity."""


class ParticipantNotSignedUpError(Exception):
    """Raised when a participant is not registered for an activity."""


class ActivityStore:
    def __init__(
        self,
        database_path: Path,
        initial_activities: Mapping[str, ActivityData],
    ) -> None:
        self.database_path = database_path
        self.initial_activities = initial_activities
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS activities (
                    name TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    max_participants INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    activity_name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    PRIMARY KEY (activity_name, email),
                    FOREIGN KEY (activity_name) REFERENCES activities(name)
                        ON DELETE CASCADE
                )
                """
            )

            has_activities = connection.execute(
                "SELECT 1 FROM activities LIMIT 1"
            ).fetchone()
            if has_activities is None:
                for name, activity in self.initial_activities.items():
                    connection.execute(
                        """
                        INSERT INTO activities
                            (name, description, schedule, max_participants)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            name,
                            activity["description"],
                            activity["schedule"],
                            activity["max_participants"],
                        ),
                    )
                    connection.executemany(
                        """
                        INSERT INTO participants (activity_name, email)
                        VALUES (?, ?)
                        """,
                        [
                            (name, email)
                            for email in activity["participants"]
                        ],
                    )

    def get_activities(self) -> dict[str, ActivityData]:
        with self._connection() as connection:
            activities = connection.execute(
                """
                SELECT name, description, schedule, max_participants
                FROM activities
                ORDER BY rowid
                """
            ).fetchall()
            participants = connection.execute(
                """
                SELECT activity_name, email
                FROM participants
                ORDER BY rowid
                """
            ).fetchall()

        participants_by_activity: dict[str, list[str]] = {}
        for participant in participants:
            participants_by_activity.setdefault(
                participant["activity_name"], []
            ).append(participant["email"])

        return {
            activity["name"]: {
                "description": activity["description"],
                "schedule": activity["schedule"],
                "max_participants": activity["max_participants"],
                "participants": participants_by_activity.get(
                    activity["name"], []
                ),
            }
            for activity in activities
        }

    def signup(self, activity_name: str, email: str) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            activity = connection.execute(
                "SELECT 1 FROM activities WHERE name = ?", (activity_name,)
            ).fetchone()
            if activity is None:
                raise ActivityNotFoundError

            participant = connection.execute(
                """
                SELECT 1 FROM participants
                WHERE activity_name = ? AND email = ?
                """,
                (activity_name, email),
            ).fetchone()
            if participant is not None:
                raise ParticipantAlreadySignedUpError

            connection.execute(
                """
                INSERT INTO participants (activity_name, email)
                VALUES (?, ?)
                """,
                (activity_name, email),
            )

    def unregister(self, activity_name: str, email: str) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            activity = connection.execute(
                "SELECT 1 FROM activities WHERE name = ?", (activity_name,)
            ).fetchone()
            if activity is None:
                raise ActivityNotFoundError

            result = connection.execute(
                """
                DELETE FROM participants
                WHERE activity_name = ? AND email = ?
                """,
                (activity_name, email),
            )
            if result.rowcount == 0:
                raise ParticipantNotSignedUpError
