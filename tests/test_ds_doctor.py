"""Tests for the ds-scheduler doctor preflight.

The doctor exists because a first-time caller who gets a bare ``DS_API_ERROR
401`` concludes the gateway is broken. Two properties matter most here:

- it must understand **both** the older bare ``DS_API_ERROR`` shape and the
  newer translated codes, so it is useful before every host has been updated;
- it must never print the token.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import ds_doctor

TOKEN = "633c1dd94f755b0c1bcbfdbb0ef9e20a"


class TokenResolutionTests(unittest.TestCase):
    def test_explicit_token_wins(self):
        token, source = ds_doctor.resolve_token("pk", ds_token=TOKEN)
        self.assertEqual(TOKEN, token)
        self.assertEqual("--ds-token", source)

    def test_token_is_returned_unstripped_so_whitespace_is_visible(self):
        # Stripping here would hide the very defect inspect_token looks for.
        token, _ = ds_doctor.resolve_token("pk", ds_token=TOKEN + "\n")
        self.assertTrue(token.endswith("\n"))

    def test_environment_variable_is_used(self):
        with mock.patch.dict(os.environ, {"DS_TOKEN_TH": TOKEN}, clear=False):
            token, source = ds_doctor.resolve_token("th")
        self.assertEqual(TOKEN, token)
        self.assertEqual("$DS_TOKEN_TH", source)

    def test_blank_token_is_not_reported_as_found(self):
        token, source = ds_doctor.resolve_token("mx", ds_token="   ")
        self.assertEqual("", token)
        self.assertEqual("", source)

    def test_default_file_is_read_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            secrets = Path(tmp)
            (secrets / "pk-dolphinscheduler-token").write_text(TOKEN, encoding="utf-8")
            with mock.patch.object(ds_doctor, "SECRETS_DIR", secrets):
                token, source = ds_doctor.resolve_token("pk")
        self.assertEqual(TOKEN, token)
        self.assertIn("pk-dolphinscheduler-token", source)

    def test_missing_token_file_is_an_error_not_a_silent_fallback(self):
        with self.assertRaises(SystemExit):
            ds_doctor.resolve_token("pk", token_file="/definitely/not/here")

    def test_token_config_matches_the_builder_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokens.json"
            path.write_text(json.dumps({"tokens": {"pk": TOKEN}}), encoding="utf-8")
            self.assertEqual(TOKEN, ds_doctor.load_token_from_config(str(path), "pk"))

    def test_token_config_expands_environment_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokens.json"
            path.write_text(json.dumps({"tokens": {"pk": "${PK_DS_TOKEN}"}}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"PK_DS_TOKEN": TOKEN}, clear=False):
                self.assertEqual(TOKEN, ds_doctor.load_token_from_config(str(path), "pk"))


class InspectTokenTests(unittest.TestCase):
    def test_clean_token_has_no_problems(self):
        self.assertEqual([], ds_doctor.inspect_token(TOKEN))

    def test_trailing_newline_is_flagged(self):
        problems = ds_doctor.inspect_token(TOKEN + "\n")
        self.assertTrue(any("换行" in p or "空白" in p for p in problems))

    def test_surrounding_spaces_are_flagged(self):
        self.assertTrue(ds_doctor.inspect_token(f"  {TOKEN}  "))

    def test_wrong_length_is_flagged(self):
        self.assertTrue(any("长度" in p for p in ds_doctor.inspect_token("abc")))

    def test_empty_token_is_flagged(self):
        self.assertTrue(ds_doctor.inspect_token(""))

    def test_mask_never_reveals_the_whole_token(self):
        masked = ds_doctor.mask(TOKEN)
        self.assertNotIn(TOKEN, masked)
        self.assertTrue(masked.startswith(TOKEN[:4]))


class DiagnoseTests(unittest.TestCase):
    def test_success_is_reported_as_a_working_chain(self):
        ok, headline, _ = ds_doctor.diagnose("pk", {"success": True, "data": {}})
        self.assertTrue(ok)
        self.assertIn("令牌有效", headline)

    def test_translated_401_gives_the_per_instance_guidance(self):
        ok, headline, steps = ds_doctor.diagnose(
            "pk",
            {"success": False, "error": {"code": "TOKEN_INVALID_OR_WRONG_INSTANCE", "message": "x"}},
        )
        self.assertFalse(ok)
        self.assertIn("401", headline)
        self.assertIn("令牌管理", steps[0])
        self.assertIn("互不相通", steps[0])

    def test_legacy_bare_ds_api_error_401_gives_the_same_guidance(self):
        # This is what every host still returns today, before the code pull.
        ok, headline, steps = ds_doctor.diagnose(
            "pk",
            {
                "success": False,
                "error": {
                    "code": "DS_API_ERROR",
                    "message": {"status": 401, "body": {"raw": ""}, "url": "http://x/y"},
                },
            },
        )
        self.assertFalse(ok)
        self.assertIn("401", headline)
        self.assertIn("令牌管理", steps[0])

    def test_403_is_reported_as_permission_not_authentication(self):
        ok, headline, steps = ds_doctor.diagnose(
            "mx", {"success": False, "error": {"code": "DS_PERMISSION_DENIED", "message": "x"}}
        )
        self.assertFalse(ok)
        self.assertIn("权限", headline)
        # Must not send the caller off to re-mint a working token.
        self.assertIn("项目", steps[0])
        self.assertNotIn("令牌管理", steps[0])

    def test_legacy_403_is_recognised(self):
        ok, headline, _ = ds_doctor.diagnose(
            "mx",
            {"success": False, "error": {"code": "DS_API_ERROR", "message": {"status": 403}}},
        )
        self.assertFalse(ok)
        self.assertIn("403", headline)

    def test_access_denial_points_at_provisioning_not_at_the_token(self):
        ok, _, steps = ds_doctor.diagnose(
            "pk",
            {"success": False, "error": {"code": "ACCESS_CLASS_DENIED", "message": "no"}},
        )
        self.assertFalse(ok)
        self.assertIn("访问策略", steps[0])
        self.assertIn("登记", steps[0])

    def test_unreachable_webhook_is_reported_as_a_link_problem(self):
        ok, headline, _ = ds_doctor.diagnose(
            "th", {"success": False, "error": {"code": "WEBHOOK_UNREACHABLE", "message": "x"}}
        )
        self.assertFalse(ok)
        self.assertIn("不可达", headline)

    def test_unknown_failure_still_surfaces_the_raw_detail(self):
        ok, headline, steps = ds_doctor.diagnose(
            "pk", {"success": False, "error": {"code": "SOMETHING_NEW", "message": "weird"}}
        )
        self.assertFalse(ok)
        self.assertIn("weird", steps[0])


class RunTests(unittest.TestCase):
    def _run(self, argv):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = ds_doctor.run(argparse.Namespace(**argv))
        return code, buffer.getvalue()

    def _base(self, **overrides):
        args = {
            "country": "pk",
            "webhook_url": ds_doctor.DEFAULT_WEBHOOK,
            "ds_token": None,
            "token_config": None,
            "token_file": None,
            "timeout": 5,
            "offline": True,
            "json": False,
        }
        args.update(overrides)
        return args

    def test_unsupported_country_fails_fast(self):
        code, out = self._run(self._base(country="us"))
        self.assertEqual(2, code)
        self.assertIn("不支持的国家", out)

    def test_missing_token_fails_with_setup_steps(self):
        with mock.patch.object(ds_doctor, "SECRETS_DIR", Path("/definitely/not/here")):
            code, out = self._run(self._base())
        self.assertEqual(1, code)
        self.assertIn("printf", out)
        self.assertIn("令牌管理", out)

    def test_offline_mode_skips_the_live_probe(self):
        code, out = self._run(self._base(ds_token=TOKEN))
        self.assertEqual(0, code)
        self.assertIn("已按 --offline 跳过", out)

    def test_whitespace_damaged_token_fails_before_any_network_call(self):
        code, out = self._run(self._base(ds_token=TOKEN + "\n"))
        self.assertEqual(1, code)
        self.assertIn("令牌格式", out)

    def test_token_is_never_printed(self):
        code, out = self._run(self._base(ds_token=TOKEN))
        self.assertNotIn(TOKEN, out)

    def test_json_mode_is_machine_readable(self):
        code, out = self._run(self._base(ds_token=TOKEN, json=True))
        payload = json.loads(out)
        self.assertEqual("pk", payload["country"])
        self.assertTrue(all(check["ok"] for check in payload["checks"]))

    def test_live_probe_failure_is_reported(self):
        with mock.patch.object(
            ds_doctor,
            "probe",
            return_value={"success": False, "error": {"code": "DS_API_ERROR", "message": {"status": 401}}},
        ):
            code, out = self._run(self._base(ds_token=TOKEN, offline=False))
        self.assertEqual(1, code)
        self.assertIn("令牌管理", out)


if __name__ == "__main__":
    unittest.main()
