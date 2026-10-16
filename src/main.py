"""Kingdom (Neverland) entrypoint — launches the Yuno Alliance Portal Streamlit app.

Kingdom builds this repo with its Python template, which copies `src/` into `/app`
and runs `python main.py`. This file boots Streamlit on the port Kingdom injects
via $PORT and serves it under the ingress prefix ($PREFIX_PATH, e.g.
/yuno-alliance-portal). The health check / liveness path configured in Kingdom is
`<PREFIX_PATH>/_stcore/health`, which Streamlit serves natively.

Secrets: the app reads `.streamlit/secrets.toml` (see secrets.toml.example). In the
container that file does not exist, so it is materialised at boot from env vars
(Kingdom env vars + Wilson secrets). Every block is optional — anything left unset
keeps its local/demo fallback.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE / "papo.py"
SECRETS = HERE / ".streamlit" / "secrets.toml"


def _mirror_kebab_env():
    """Wilson secret keys may arrive kebab-cased (anthropic-api-key). Mirror them
    to CONSTANT_CASE (ANTHROPIC_API_KEY) so lookups below work either way."""
    for k, v in list(os.environ.items()):
        if "-" in k:
            os.environ.setdefault(k.replace("-", "_").upper(), v)


def _toml_str(value):
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _write_secrets():
    """Build .streamlit/secrets.toml from env vars. Only emits the blocks that
    have at least one value set, so unset integrations stay in demo mode."""
    if SECRETS.exists():
        return
    env = os.environ.get
    blocks = []

    # External SSO (st.login). Needs redirect_uri + cookie_secret + one provider.
    if env("AUTH_COOKIE_SECRET"):
        redirect = env("AUTH_REDIRECT_URI") or ""
        if not redirect and env("PUBLIC_URL"):
            redirect = env("PUBLIC_URL").rstrip("/") + "/oauth2callback"
        blocks.append(
            "[auth]\n"
            f"redirect_uri = {_toml_str(redirect)}\n"
            f"cookie_secret = {_toml_str(env('AUTH_COOKIE_SECRET'))}\n"
        )
        if env("GOOGLE_CLIENT_ID") and env("GOOGLE_CLIENT_SECRET"):
            blocks.append(
                "[auth.google]\n"
                f"client_id = {_toml_str(env('GOOGLE_CLIENT_ID'))}\n"
                f"client_secret = {_toml_str(env('GOOGLE_CLIENT_SECRET'))}\n"
                'server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"\n'
            )

    # Slack alerts (webhook or bot token).
    if env("SLACK_WEBHOOK_URL") or env("SLACK_BOT_TOKEN"):
        blocks.append(
            "[slack]\n"
            f"channel = {_toml_str(env('SLACK_CHANNEL', '#partnerships-only-visibility-integrations'))}\n"
            f"webhook_url = {_toml_str(env('SLACK_WEBHOOK_URL', ''))}\n"
            f"bot_token = {_toml_str(env('SLACK_BOT_TOKEN', ''))}\n"
            f"leads_channel = {_toml_str(env('SLACK_LEADS_CHANNEL', '#partnership-leads'))}\n"
        )

    # Optional Claude enrichment for the connector search box.
    if env("ANTHROPIC_API_KEY"):
        blocks.append(
            "[anthropic]\n"
            f"api_key = {_toml_str(env('ANTHROPIC_API_KEY'))}\n"
            f"model = {_toml_str(env('ANTHROPIC_MODEL', 'claude-opus-5'))}\n"
        )

    if not blocks:
        print("[entrypoint] no secrets set — running in demo mode")
        return
    SECRETS.parent.mkdir(parents=True, exist_ok=True)
    SECRETS.write_text("\n".join(blocks))
    print(f"[entrypoint] wrote {SECRETS} ({len(blocks)} block(s))")


def main():
    _mirror_kebab_env()
    _write_secrets()

    port = os.environ.get("PORT", "8080")
    # Kingdom serves the app under a path prefix (e.g. /yuno-alliance-portal).
    # Streamlit must know it so assets and the websocket resolve under the prefix.
    base_url_path = os.environ.get("BASE_URL_PATH")
    if base_url_path is None:
        base_url_path = os.environ.get("PREFIX_PATH", "")

    args = [
        sys.executable, "-m", "streamlit", "run", str(APP),
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        # Behind the Kingdom ingress/proxy.
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
    ]
    if base_url_path.strip("/"):
        args += ["--server.baseUrlPath", base_url_path.strip("/")]
    print(f"[entrypoint] launching Streamlit on 0.0.0.0:{port} (baseUrlPath={base_url_path!r})")
    os.chdir(HERE)
    os.execvp(args[0], args)


if __name__ == "__main__":
    main()
