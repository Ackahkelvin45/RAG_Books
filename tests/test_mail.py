import httpx
import pytest

from shepherd import mail


def test_without_key_prints_instead_of_sending(monkeypatch, capsys):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: pytest.fail("must not call Resend"))
    mail.send("a@x.org", "Your code: 123456", "body 123456")
    assert "[DEV EMAIL to a@x.org] Your code: 123456" in capsys.readouterr().out


def test_sends_through_resend_api(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("MAIL_FROM", "First Love Church <no-reply@firstlove.test>")
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, headers=headers, json=json)
        return httpx.Response(200, json={"id": "e1"}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    mail.send("a@x.org", "Subj", "Body")
    assert seen["url"] == "https://api.resend.com/emails"
    assert seen["headers"]["Authorization"] == "Bearer re_test"
    assert seen["json"] == {"from": "First Love Church <no-reply@firstlove.test>", "to": ["a@x.org"], "subject": "Subj", "text": "Body"}


def test_resend_error_is_raised(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_bad")
    monkeypatch.setattr(httpx, "post", lambda url, **k: httpx.Response(403, json={"message": "domain not verified"}, request=httpx.Request("POST", url)))
    with pytest.raises(httpx.HTTPStatusError):
        mail.send("a@x.org", "S", "B")


def test_templates_carry_code_and_escape_names():
    from shepherd import emails
    subj, text, html = emails.otp_email("042917", 10)
    assert "042917" in subj and "042917" in text and "0&nbsp;4&nbsp;2&nbsp;9&nbsp;1&nbsp;7" in html and "10 minutes" in html
    subj, text, html = emails.welcome_email("<b>Ama</b>", "shepherd")
    assert "<b>Ama</b>" not in html and "&lt;b&gt;Ama&lt;/b&gt;" in html
    assert "As a shepherd" in text and "dagbooks.org" in html


def test_html_is_passed_to_resend(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    seen = {}
    monkeypatch.setattr(httpx, "post", lambda url, headers, json, timeout: (seen.update(json), httpx.Response(200, json={}, request=httpx.Request("POST", url)))[1])
    mail.send("a@x.org", "S", "text", "<p>html</p>")
    assert seen["html"] == "<p>html</p>" and seen["text"] == "text"
