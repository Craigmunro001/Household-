import httpx

import preflight


FULL = {"WHATSAPP_TOKEN": "t", "WHATSAPP_PHONE_NUMBER_ID": "1", "WHATSAPP_VERIFY_TOKEN": "v", "WHATSAPP_APP_SECRET": "s",
        "ANTHROPIC_API_KEY": "k", "GOOGLE_SHEET_ID": "g", "GOOGLE_SERVICE_ACCOUNT_JSON": "{}", "NOTIFY_TO": "a@b.c",
        "SMTP_HOST": "h", "SMTP_USER": "u", "SMTP_PASSWORD": "p", "DB_PATH": "/data/sessions.sqlite3"}


def statuses(rows):
    return {name: status for status, name, _ in rows}


def test_everything_present_has_no_failures_or_warnings():
    assert all(s == preflight.OK for s in statuses(preflight.check_env(FULL)).values())


def test_missing_required_settings_block_go_live_and_say_why():
    rows = preflight.check_env({})
    st = statuses(rows)
    for name in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID", "WHATSAPP_VERIFY_TOKEN", "WHATSAPP_APP_SECRET"):
        assert st[name] == preflight.FAIL
    assert any("Meta" in detail for _, n, detail in rows if n == "WHATSAPP_TOKEN")


def test_missing_optional_settings_only_warn():
    st = statuses(preflight.check_env({k: v for k, v in FULL.items() if k not in ("ANTHROPIC_API_KEY", "GOOGLE_SHEET_ID")}))
    assert st["ANTHROPIC_API_KEY"] == preflight.WARN and st["GOOGLE_SHEET_ID"] == preflight.WARN


def test_dev_mode_in_production_is_a_blocking_problem():
    assert statuses(preflight.check_env({**FULL, "DEV_MODE": "1"}))["DEV_MODE"] == preflight.FAIL


def test_database_off_a_volume_warns():
    assert statuses(preflight.check_env({**FULL, "DB_PATH": "data/sessions.sqlite3"}))["DB_PATH"] == preflight.WARN


def test_secret_values_are_never_printed(capsys):
    import os
    old = dict(os.environ)
    os.environ.update({k: "SUPERSECRETVALUE" for k in FULL if k != "DB_PATH"})  # the DB path is shown on purpose; it is not a secret
    try:
        preflight.main([])
    finally:
        os.environ.clear()
        os.environ.update(old)
    assert "SUPERSECRETVALUE" not in capsys.readouterr().out


def test_content_checks_pass_in_this_repo():
    st = statuses(preflight.check_content())
    assert st["price book"] == preflight.OK and st["FAQ knowledge"] == preflight.OK


def fake_server(verify_token="v", sig_enforced=True, health=None):
    def handler(request):
        path = request.url.path
        if path == "/health":
            return httpx.Response(200, json=health or {"ok": True, "llm": True, "sheet": "GoogleSheetSink", "price_book": "2 November 2026"})
        if path == "/webhook" and request.method == "GET":
            ok = request.url.params.get("hub.verify_token") == verify_token
            return httpx.Response(200, text=request.url.params.get("hub.challenge")) if ok else httpx.Response(403)
        return httpx.Response(403 if sig_enforced else 200, json={})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_deployed_app_that_is_healthy_passes_every_check():
    rows = preflight.check_url("https://x.example", "v", fake_server())
    assert all(s == preflight.OK for s, _, _ in rows), rows


def test_wrong_verify_token_is_caught_before_meta_does():
    st = statuses(preflight.check_url("https://x.example", "different", fake_server(verify_token="v")))
    assert st["webhook handshake"] == preflight.FAIL


def test_a_server_that_accepts_unsigned_webhooks_is_flagged_as_a_security_problem():
    st = statuses(preflight.check_url("https://x.example", "v", fake_server(sig_enforced=False)))
    assert st["unsigned webhook rejected"] == preflight.FAIL


def test_unreachable_server_is_reported_not_crashed():
    def boom(request):
        raise httpx.ConnectError("no route")
    rows = preflight.check_url("https://x.example", "v", httpx.Client(transport=httpx.MockTransport(boom)))
    assert rows[0][0] == preflight.FAIL


def test_the_default_whatsapp_api_version_is_not_one_that_meta_is_about_to_retire():
    from app.config import get_settings
    get_settings.cache_clear()
    assert get_settings().wa_api_version not in ("v20.0", "v21.0")
