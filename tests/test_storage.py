import tempfile
import unittest
from pathlib import Path

from src.storage import (
    ActivityData,
    ActivityNotFoundError,
    ActivityStore,
    ParticipantAlreadySignedUpError,
    ParticipantNotSignedUpError,
)


INITIAL_ACTIVITIES: dict[str, ActivityData] = {
    "Chess Club": {
        "description": "Play chess",
        "schedule": "Fridays",
        "max_participants": 12,
        "participants": ["student@mergington.edu"],
    }
}


class ActivityStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "activities.sqlite"
        self.store = ActivityStore(self.database_path, INITIAL_ACTIVITIES)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_seeds_initial_activities_and_participants(self) -> None:
        self.assertEqual(self.store.get_activities(), INITIAL_ACTIVITIES)

    def test_signup_and_unregister_survive_store_recreation(self) -> None:
        self.store.signup("Chess Club", "new@mergington.edu")
        recreated_store = ActivityStore(
            self.database_path,
            {
                "Different Activity": {
                    "description": "Should not be seeded",
                    "schedule": "Never",
                    "max_participants": 1,
                    "participants": [],
                }
            },
        )
        self.assertEqual(
            recreated_store.get_activities()["Chess Club"]["participants"],
            ["student@mergington.edu", "new@mergington.edu"],
        )

        recreated_store.unregister("Chess Club", "student@mergington.edu")
        self.assertEqual(
            ActivityStore(self.database_path, INITIAL_ACTIVITIES)
            .get_activities()["Chess Club"]["participants"],
            ["new@mergington.edu"],
        )

    def test_signup_rejects_unknown_activities_and_duplicates(self) -> None:
        with self.assertRaises(ActivityNotFoundError):
            self.store.signup("Unknown Activity", "student@mergington.edu")
        with self.assertRaises(ParticipantAlreadySignedUpError):
            self.store.signup("Chess Club", "student@mergington.edu")

    def test_unregister_rejects_unknown_activities_and_participants(self) -> None:
        with self.assertRaises(ActivityNotFoundError):
            self.store.unregister("Unknown Activity", "student@mergington.edu")
        with self.assertRaises(ParticipantNotSignedUpError):
            self.store.unregister("Chess Club", "unknown@mergington.edu")


if __name__ == "__main__":
    unittest.main()
