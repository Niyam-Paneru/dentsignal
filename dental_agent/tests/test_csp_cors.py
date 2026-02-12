"""
test_csp_cors.py - CSP & CORS Hardening Tests (AG-7)

Tests:
1. API endpoints return strict CSP (default-src 'none', no unsafe-inline/eval)
2. Docs endpoints (/docs, /redoc) return relaxed but safe CSP
3. All responses include required security headers (COOP, CORP, X-Frame-Options, etc.)
4. CORS rejects unknown origins
5. CORS allows configured origins with correct headers
6. CORS wildcard '*' is blocked
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """FastAPI test client."""
    from api_main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_csp(header_value: str) -> dict[str, str]:
    """Parse a CSP header into a directive -> value dict."""
    directives = {}
    for part in header_value.split(";"):
        part = part.strip()
        if not part:
            continue
        tokens = part.split(None, 1)
        name = tokens[0]
        value = tokens[1] if len(tokens) > 1 else ""
        directives[name] = value
    return directives


# ===========================================================================
# 1. API CSP Tests
# ===========================================================================

class TestApiCsp:
    """CSP on regular API endpoints (non-docs)."""

    def test_api_csp_present(self, client):
        """API responses must include a Content-Security-Policy header."""
        r = client.get("/health")
        assert "content-security-policy" in r.headers

    def test_api_csp_default_none(self, client):
        """API CSP must set default-src to 'none'."""
        csp = _parse_csp(r.headers["content-security-policy"]) if (r := client.get("/health")) else {}
        assert csp.get("default-src") == "'none'"

    def test_api_csp_no_unsafe_inline(self, client):
        """API CSP must NOT contain 'unsafe-inline' in any directive."""
        r = client.get("/health")
        csp_raw = r.headers["content-security-policy"].lower()
        assert "unsafe-inline" not in csp_raw

    def test_api_csp_no_unsafe_eval(self, client):
        """API CSP must NOT contain 'unsafe-eval' in any directive."""
        r = client.get("/health")
        csp_raw = r.headers["content-security-policy"].lower()
        assert "unsafe-eval" not in csp_raw

    def test_api_csp_frame_ancestors_none(self, client):
        """API CSP blocks all framing via frame-ancestors 'none'."""
        r = client.get("/health")
        csp = _parse_csp(r.headers["content-security-policy"])
        assert csp.get("frame-ancestors") == "'none'"

    def test_api_csp_base_uri_none(self, client):
        """API CSP restricts base-uri to 'none'."""
        r = client.get("/health")
        csp = _parse_csp(r.headers["content-security-policy"])
        assert csp.get("base-uri") == "'none'"

    def test_api_csp_form_action_none(self, client):
        """API CSP restricts form-action to 'none'."""
        r = client.get("/health")
        csp = _parse_csp(r.headers["content-security-policy"])
        assert csp.get("form-action") == "'none'"

    @pytest.mark.parametrize("path", ["/health", "/api/v1/auth/login"])
    def test_api_endpoints_use_strict_csp(self, client, path):
        """Multiple API paths must all use the strict CSP."""
        r = client.get(path) if path == "/health" else client.post(path, json={})
        csp_raw = r.headers.get("content-security-policy", "")
        assert "default-src 'none'" in csp_raw


# ===========================================================================
# 2. Docs CSP Tests
# ===========================================================================

class TestDocsCsp:
    """CSP on documentation endpoints (/docs, /redoc, /openapi.json)."""

    @pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
    def test_docs_csp_present(self, client, path):
        """Docs endpoints must include a CSP header."""
        r = client.get(path)
        assert "content-security-policy" in r.headers

    def test_docs_csp_allows_cdn(self, client):
        """Docs CSP allows cdn.jsdelivr.net for script/style (Swagger UI)."""
        r = client.get("/docs")
        csp_raw = r.headers["content-security-policy"]
        assert "cdn.jsdelivr.net" in csp_raw

    def test_docs_csp_no_unsafe_inline(self, client):
        """Docs CSP must NOT contain 'unsafe-inline'."""
        r = client.get("/docs")
        csp_raw = r.headers["content-security-policy"].lower()
        assert "unsafe-inline" not in csp_raw

    def test_docs_csp_no_unsafe_eval(self, client):
        """Docs CSP must NOT contain 'unsafe-eval'."""
        r = client.get("/docs")
        csp_raw = r.headers["content-security-policy"].lower()
        assert "unsafe-eval" not in csp_raw

    def test_docs_csp_default_none(self, client):
        """Docs CSP also sets default-src 'none'."""
        r = client.get("/docs")
        csp = _parse_csp(r.headers["content-security-policy"])
        assert csp.get("default-src") == "'none'"


# ===========================================================================
# 3. Security Headers Tests
# ===========================================================================

class TestSecurityHeaders:
    """All responses must include standard security headers."""

    def test_x_content_type_options(self, client):
        r = client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        r = client.get("/health")
        assert r.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection_disabled(self, client):
        """X-XSS-Protection should be '0' (modern best practice — CSP replaces it)."""
        r = client.get("/health")
        assert r.headers.get("x-xss-protection") == "0"

    def test_referrer_policy(self, client):
        r = client.get("/health")
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_cross_origin_opener_policy(self, client):
        r = client.get("/health")
        assert r.headers.get("cross-origin-opener-policy") == "same-origin"

    def test_cross_origin_resource_policy(self, client):
        r = client.get("/health")
        assert r.headers.get("cross-origin-resource-policy") == "same-origin"

    def test_permissions_policy(self, client):
        r = client.get("/health")
        pp = r.headers.get("permissions-policy", "")
        for feature in ("camera=()", "microphone=()", "geolocation=()"):
            assert feature in pp

    @pytest.mark.parametrize("header", [
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
        "referrer-policy",
        "content-security-policy",
        "cross-origin-opener-policy",
        "cross-origin-resource-policy",
        "permissions-policy",
    ])
    def test_header_present_on_all_responses(self, client, header):
        """Every response from the API must include the security header."""
        r = client.get("/health")
        assert header in r.headers, f"Missing header: {header}"


# ===========================================================================
# 4. CORS Tests
# ===========================================================================

class TestCors:
    """CORS configuration must allow configured origins and reject others."""

    def test_cors_allows_configured_origin(self, client):
        """Configured origin receives proper CORS headers."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"

    def test_cors_rejects_unknown_origin(self, client):
        """Unknown origin does NOT receive access-control-allow-origin."""
        r = client.options(
            "/health",
            headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI CORSMiddleware simply omits the header for disallowed origins
        acao = r.headers.get("access-control-allow-origin", "")
        assert "evil.com" not in acao

    def test_cors_preflight_allows_expected_methods(self, client):
        """Preflight response lists the allowed HTTP methods."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            },
        )
        allowed = r.headers.get("access-control-allow-methods", "")
        for method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            assert method in allowed

    def test_cors_preflight_allows_expected_headers(self, client):
        """Preflight lists the allowed request headers."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        allowed_headers = r.headers.get("access-control-allow-headers", "").lower()
        assert "authorization" in allowed_headers

    def test_cors_credentials_allowed(self, client):
        """Credentials are allowed for configured origins."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.headers.get("access-control-allow-credentials") == "true"

    def test_cors_max_age(self, client):
        """Preflight cache max-age is set."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        max_age = r.headers.get("access-control-max-age", "")
        assert max_age == "600"

    def test_cors_no_wildcard_origin(self, client):
        """CORS never returns '*' as allowed origin (incompatible with credentials)."""
        r = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert r.headers.get("access-control-allow-origin") != "*"
