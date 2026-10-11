import json
import os
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

from app import app

COVERED_ROUTES = {
    ("/activities", "GET"),
    ("/activities", "POST"),
    ("/calories", "GET"),
    ("/log", "POST"),
    ("/log/undo", "POST"),
    ("/notices", "GET"),
    ("/stats", "GET"),
    ("/targets", "GET"),
    ("/user", "POST"),
}

SEDENTARY_MALE_TARGETS = {
    "calories": 2134,
    "protein_g": 128.0,
    "carbohydrates_g": 272.1,
    "fat_g": 59.3,
}


class DietFlowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activities_path = ROOT / "data" / "activities.json"
        cls.logs_path = ROOT / "data" / "logs.json"
        cls.notices_path = ROOT / "data" / "notices.json"
        cls.user_path = ROOT / "data" / "user.json"
        cls.original_activities = cls.activities_path.read_text()
        cls.original_logs = cls.logs_path.read_text()
        cls.original_notices = (
            cls.notices_path.read_text() if cls.notices_path.exists() else None
        )
        cls.original_user = (
            cls.user_path.read_text() if cls.user_path.exists() else None
        )
        cls.catalog = json.loads(cls.original_activities)

    def setUp(self):
        self.client = app.test_client()
        self.activities_path.write_text(self.original_activities)
        self.logs_path.write_text("[]\n")
        self.notices_path.write_text("[]\n")
        if self.user_path.exists():
            self.user_path.unlink()

    def tearDown(self):
        self.activities_path.write_text(self.original_activities)
        self.logs_path.write_text(self.original_logs)
        if self.original_notices is None:
            self.notices_path.unlink(missing_ok=True)
        else:
            self.notices_path.write_text(self.original_notices)
        if self.original_user is None:
            self.user_path.unlink(missing_ok=True)
        else:
            self.user_path.write_text(self.original_user)

    def test_every_route_is_covered(self):
        found = set()
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith("/static"):
                continue
            for method in rule.methods:
                if method in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                    found.add((rule.rule, method))
        self.assertEqual(found, COVERED_ROUTES)

    def test_activities_catalog_and_validation(self):
        listed = self.client.get("/activities")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(
            {row["name"]: row["calories_per_60_min"] for row in listed.get_json()},
            {row["name"]: row["calories_per_60_min"] for row in self.catalog},
        )

        self.assertEqual(
            self.client.post(
                "/activities", data="nope", content_type="text/plain"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/activities", json={"name": "boxing"}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                "/activities", json={"name": "  ", "calories_per_60_min": 100}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/activities", json={"name": "boxing", "calories_per_60_min": 0}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/activities", json={"name": "boxing", "calories_per_60_min": "lots"}
            ).status_code,
            400,
        )
        self.assertEqual(
            len(self.client.get("/activities").get_json()), len(self.catalog)
        )

        created = self.client.post(
            "/activities", json={"name": " boxing ", "calories_per_60_min": "540"}
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.get_json()["name"], "boxing")
        self.assertEqual(created.get_json()["calories_per_60_min"], 540)

        rows = self.client.get("/activities").get_json()
        self.assertEqual(len(rows), len(self.catalog) + 1)
        boxing = next(row for row in rows if row["name"] == "boxing")
        self.assertEqual(boxing["calories_per_60_min"], 540)

        duplicate = self.client.post(
            "/activities", json={"name": "boxing", "calories_per_60_min": 100}
        )
        self.assertEqual(duplicate.status_code, 400)
        boxing = next(
            row
            for row in self.client.get("/activities").get_json()
            if row["name"] == "boxing"
        )
        self.assertEqual(boxing["calories_per_60_min"], 540)

        logged = self.client.post("/log", json={"type": "boxing", "minutes": 30})
        self.assertEqual(logged.status_code, 201)
        self.assertEqual(logged.get_json()["calories"], 270)

    def test_log_notices_and_undo(self):
        self.assertEqual(self.client.post("/log/undo").status_code, 400)
        self.assertEqual(self.client.get("/notices").get_json(), [])

        self.assertEqual(
            self.client.post("/log", data="x", content_type="text/plain").status_code,
            400,
        )
        self.assertEqual(
            self.client.post("/log", json={"minutes": 10}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                "/log", json={"type": "running", "minutes": 0}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/log", json={"type": "running", "minutes": -5}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/log", json={"type": "running", "minutes": "nope"}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/log", json={"type": "napping", "minutes": 10}
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/notices").get_json(), [])
        self.assertEqual(
            self.client.get("/calories?period=week").get_json()["count"], 0
        )

        walking = self.client.post("/log", json={"type": "walking", "minutes": "40"})
        self.assertEqual(walking.status_code, 201)
        self.assertEqual(walking.get_json()["minutes"], 40)
        self.assertEqual(walking.get_json()["calories"], 187)
        self.assertEqual(walking.get_json()["weekly_calories"], 187)
        self.assertEqual(walking.get_json()["weekly_goal"], 500)
        self.assertFalse(walking.get_json()["goal_reached"])

        running = self.client.post("/log", json={"type": "running", "minutes": 60})
        self.assertEqual(running.status_code, 201)
        self.assertEqual(running.get_json()["calories"], 600)
        self.assertEqual(running.get_json()["weekly_calories"], 787)
        self.assertTrue(running.get_json()["goal_reached"])

        notices = self.client.get("/notices").get_json()
        self.assertEqual(
            [row["event"] for row in notices],
            ["activity_logged", "activity_logged", "weekly_goal_reached"],
        )
        self.assertEqual(notices[0]["type"], "walking")
        self.assertEqual(notices[0]["calories"], 187)
        self.assertEqual(notices[1]["type"], "running")
        self.assertEqual(notices[2]["calories"], 787)
        self.assertEqual(notices[2]["goal"], 500)

        undone = self.client.post("/log/undo")
        self.assertEqual(undone.status_code, 200)
        self.assertEqual(undone.get_json()["type"], "running")
        self.assertEqual(undone.get_json()["minutes"], 60)
        self.assertEqual(
            self.client.get("/calories?period=day").get_json()["total_calories"], 187
        )
        self.assertEqual(len(self.client.get("/notices").get_json()), 3)

        self.assertEqual(self.client.post("/log/undo").status_code, 200)
        self.assertEqual(self.client.post("/log/undo").status_code, 400)
        self.assertEqual(
            self.client.get("/calories?period=week").get_json()["total_calories"], 0
        )

    def test_calorie_periods(self):
        empty = self.client.get("/calories?period=week")
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.get_json()["total_calories"], 0)
        self.assertEqual(empty.get_json()["count"], 0)
        self.assertEqual(empty.get_json()["logs"], [])
        self.assertEqual(self.client.get("/calories").status_code, 400)
        self.assertEqual(self.client.get("/calories?period=year").status_code, 400)

        now = datetime.now().replace(microsecond=0)
        self.logs_path.write_text(
            json.dumps(
                [
                    {
                        "type": "running",
                        "minutes": 30,
                        "logged_at": (now - timedelta(hours=1)).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                    },
                    {
                        "type": "cycling",
                        "minutes": 45,
                        "logged_at": (now - timedelta(days=10)).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                    },
                    {
                        "type": "yoga",
                        "minutes": 50,
                        "logged_at": (now - timedelta(days=40)).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                    },
                    {
                        "type": "not_a_real_activity",
                        "minutes": 20,
                        "logged_at": (now - timedelta(hours=1)).strftime(
                            "%Y-%m-%dT%H:%M:%S"
                        ),
                    },
                ],
                indent=2,
            )
        )

        day = self.client.get("/calories?period=day").get_json()
        week = self.client.get("/calories?period=week").get_json()
        month = self.client.get("/calories?period=month").get_json()

        self.assertEqual(day["period"], "day")
        self.assertEqual([row["type"] for row in day["logs"]], ["running"])
        self.assertEqual(day["total_calories"], 300)
        self.assertEqual(day["count"], 1)

        self.assertEqual(week["period"], "week")
        self.assertEqual([row["type"] for row in week["logs"]], ["running"])
        self.assertEqual(week["total_calories"], 300)

        self.assertEqual(month["period"], "month")
        self.assertEqual([row["type"] for row in month["logs"]], ["running", "cycling"])
        self.assertEqual(month["total_calories"], 660)
        self.assertEqual(month["count"], 2)

        for body in (day, week, month):
            self.assertIn("from", body)
            self.assertIn("to", body)
            self.assertEqual(
                sum(row["calories"] for row in body["logs"]), body["total_calories"]
            )

    def test_user_profile_validation(self):
        self.assertEqual(self.client.get("/targets").status_code, 400)
        self.assertEqual(self.client.get("/targets?period=year").status_code, 400)
        self.assertEqual(self.client.get("/targets?period=week").status_code, 400)

        self.assertEqual(
            self.client.post(
                "/user?age=28&gender=male&weight_kg=80&height_cm=178"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/user?age=28&gender=other&weight_kg=80&height_cm=178&goal=maintain"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/user?age=28&gender=male&weight_kg=80&height_cm=178&goal=bulk"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/user?age=0&gender=male&weight_kg=80&height_cm=178&goal=lose"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/user?age=28&gender=male&weight_kg=heavy&height_cm=178&goal=maintain"
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/targets?period=week").status_code, 400)

        saved = self.save_male()
        self.assertEqual(
            saved,
            {
                "age": 28,
                "gender": "male",
                "weight_kg": 80,
                "height_cm": 178,
                "goal": "maintain",
            },
        )
        self.assertEqual(
            self.client.post(
                "/user?age=0&gender=male&weight_kg=80&height_cm=178&goal=maintain"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/user?age=28&gender=other&weight_kg=80&height_cm=178&goal=maintain"
            ).status_code,
            400,
        )

        body = self.targets("week")
        self.assertEqual(body["calories_burned"], 0)
        self.assertEqual(body["weekly_calories"], 0)
        self.assert_sedentary_male(body)

    def test_user_logs_activities_then_gets_diet_targets(self):
        self.assertEqual(
            self.save_male(),
            {
                "age": 28,
                "gender": "male",
                "weight_kg": 80,
                "height_cm": 178,
                "goal": "maintain",
            },
        )

        running = self.client.post("/log", json={"type": "running", "minutes": 30})
        self.assertEqual(running.status_code, 201)
        self.assertEqual(running.get_json()["calories"], 300)

        walking = self.client.post("/log", json={"type": "walking", "minutes": 40})
        self.assertEqual(walking.status_code, 201)
        self.assertEqual(walking.get_json()["calories"], 187)

        burned = self.client.get("/calories?period=week").get_json()
        self.assertEqual(
            [row["type"] for row in burned["logs"]], ["running", "walking"]
        )
        self.assertEqual(burned["total_calories"], 487)

        week = self.targets("week")
        self.assert_sedentary_male(week)
        self.assertEqual(week["calories_burned"], 487)
        self.assertEqual(week["weekly_calories"], 487)

        day = self.targets("day")
        self.assert_sedentary_male(day)
        self.assertEqual(day["calories_burned"], 487)
        self.assertEqual(day["weekly_calories"], 487 * 7)

        month = self.targets("month")
        self.assert_sedentary_male(month)
        self.assertEqual(month["calories_burned"], 487)
        self.assertEqual(month["weekly_calories"], int(round(487 * 7 / 30)))

    def test_high_training_week_changes_activity_level(self):
        self.save_male()
        logged = self.client.post("/log", json={"type": "running", "minutes": 1775})
        self.assertEqual(logged.status_code, 201)
        self.assertEqual(logged.get_json()["calories"], 17750)
        self.assertGreaterEqual(logged.get_json()["weekly_calories"], 17745)

        body = self.targets("week")
        self.assertEqual(body["activity_level"], "very active")
        self.assertEqual(body["activity"], "extra_active")
        self.assertEqual(body["bmr"], 1778)
        self.assertEqual(body["calories_burned"], 17750)
        self.assertGreater(body["tdee"], 2134)
        self.assertEqual(body["daily_targets"]["calories"], body["tdee"])
        for key in ("protein_g", "carbohydrates_g", "fat_g"):
            self.assertGreater(body["daily_targets"][key], 0)

    def test_request_stats(self):
        before = self.client.get("/stats")
        self.assertEqual(before.status_code, 200)
        self.assertEqual(before.get_json()["last_path"], "/stats")
        self.assertGreaterEqual(before.get_json()["count"], 1)

        self.client.get("/activities")
        after = self.client.get("/stats").get_json()
        self.assertEqual(after["count"], before.get_json()["count"] + 2)
        self.assertEqual(after["last_path"], "/stats")
        self.assertGreaterEqual(after["last_seconds"], 0)

    def save_male(self):
        saved = self.client.post(
            "/user?age=28&gender=male&weight_kg=80&height_cm=178&goal=maintain"
        )
        self.assertEqual(saved.status_code, 200, saved.get_json())
        return saved.get_json()

    def targets(self, period):
        response = None
        for attempt in range(4):
            time.sleep(1.3)
            response = self.client.get("/targets?period=" + period)
            if response.status_code != 502:
                break
            time.sleep(2 * (attempt + 1))
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()

    def assert_sedentary_male(self, body):
        self.assertEqual(body["activity_level"], "not active")
        self.assertEqual(body["activity"], "sedentary")
        self.assertEqual(body["bmr"], 1778)
        self.assertEqual(body["tdee"], 2134)
        self.assertEqual(body["daily_targets"], SEDENTARY_MALE_TARGETS)


if __name__ == "__main__":
    unittest.main()
