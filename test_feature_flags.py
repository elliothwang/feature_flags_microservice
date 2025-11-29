import os
import unittest

from app import (
    create_app,
    FLAGS,
    ALLOWED_MODES,
    ENVIRONMENT_FLAG_NAME,
    _initialize_flags,
)


class FeatureFlagServiceTests(unittest.TestCase):
    """
    integration-style tests for the feature flag microservice using the flask test client
    """

    def setUp(self):
        # ensure a known default mode for each test
        os.environ["FEATURE_FLAG_DEFAULT_MODE"] = "test"
        _initialize_flags()

        self.app = create_app()
        self.client = self.app.test_client()

    # ------------------------
    # helpers
    # ------------------------

    def _get_mode(self):
        resp = self.client.get("/mode")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        return data.get("mode")

    # ------------------------
    # tests
    # ------------------------

    def test_health_endpoint_reports_ok_and_mode(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "feature-flag")

        mode = data.get("mode")
        self.assertIn(mode, ALLOWED_MODES)

    def test_get_all_flags_returns_environment_mode_flag(self):
        resp = self.client.get("/flags")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")

        flags = data.get("flags", {})
        self.assertIn(ENVIRONMENT_FLAG_NAME, flags)
        self.assertIn(flags[ENVIRONMENT_FLAG_NAME], ALLOWED_MODES)

    def test_get_single_flag_existing(self):
        # ensure known value
        FLAGS[ENVIRONMENT_FLAG_NAME] = "test"

        resp = self.client.get(f"/flags/{ENVIRONMENT_FLAG_NAME}")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("name"), ENVIRONMENT_FLAG_NAME)
        self.assertEqual(data.get("value"), "test")

    def test_get_single_flag_missing_returns_404(self):
        resp = self.client.get("/flags/does_not_exist")
        self.assertEqual(resp.status_code, 404)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("not found", data.get("message", "").lower())

    def test_create_generic_flag_success(self):
        payload = {"name": "enable_new_layout", "value": True}
        resp = self.client.post("/flags", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("name"), "enable_new_layout")
        self.assertTrue(data.get("value"))

        # confirm it is persisted
        resp_get = self.client.get("/flags/enable_new_layout")
        self.assertEqual(resp_get.status_code, 200)
        data_get = resp_get.get_json()
        self.assertEqual(data_get.get("value"), True)

    def test_create_flag_rejects_missing_name(self):
        payload = {"value": True}
        resp = self.client.post("/flags", json=payload)
        self.assertEqual(resp.status_code, 400)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("name", data.get("message", "").lower())

    def test_create_flag_rejects_missing_value(self):
        payload = {"name": "some_flag"}
        resp = self.client.post("/flags", json=payload)
        self.assertEqual(resp.status_code, 400)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("value", data.get("message", "").lower())

    def test_environment_mode_flag_rejects_invalid_values(self):
        # via /flags
        payload = {"name": ENVIRONMENT_FLAG_NAME, "value": "invalid_mode"}
        resp = self.client.post("/flags", json=payload)
        self.assertEqual(resp.status_code, 400)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("environment_mode", data.get("message", ""))

        # mode should still be a valid one
        mode = FLAGS.get(ENVIRONMENT_FLAG_NAME)
        self.assertIn(mode, ALLOWED_MODES)

    def test_mode_get_endpoint_matches_environment_flag(self):
        FLAGS[ENVIRONMENT_FLAG_NAME] = "test"

        resp = self.client.get("/mode")
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("mode"), "test")

    def test_mode_post_updates_environment_flag(self):
        # switch to production via /mode
        resp = self.client.post("/mode", json={"mode": "production"})
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("mode"), "production")

        # /mode get should now reflect the change
        resp_get = self.client.get("/mode")
        self.assertEqual(resp_get.status_code, 200)
        self.assertEqual(resp_get.get_json().get("mode"), "production")

        # /flags/<environment_mode> should also match
        resp_flag = self.client.get(f"/flags/{ENVIRONMENT_FLAG_NAME}")
        self.assertEqual(resp_flag.status_code, 200)
        self.assertEqual(resp_flag.get_json().get("value"), "production")

    def test_mode_post_rejects_invalid_values(self):
        resp = self.client.post("/mode", json={"mode": "prod"})
        self.assertEqual(resp.status_code, 400)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("invalid mode", data.get("message", "").lower())

    def test_404_handler_returns_json_error(self):
        resp = self.client.get("/this/does/not/exist")
        self.assertEqual(resp.status_code, 404)

        data = resp.get_json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("endpoint not found", data.get("message", "").lower())


if __name__ == "__main__":
    # running as a script will execute all tests and exit with pass/fail status
    unittest.main()
