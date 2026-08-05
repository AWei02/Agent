"""Reconciles admin-managed Feishu applications into long-connection workers."""
from __future__ import annotations
import asyncio, logging, multiprocessing, os, time
from datetime import UTC, datetime
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models import ApiKey, FeishuApplication
from app.services.feishu_secrets import decrypt_secret
from workers.feishu_bot import BotConfig, FeishuBot

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
LOG = logging.getLogger('deep_agents.feishu_manager')
POLL_SECONDS = 5

def run_connection(config: BotConfig) -> None:
    FeishuBot(config).run()

class Manager:
    def __init__(self):
        self.children: dict[str, multiprocessing.Process] = {}
        self._lock = asyncio.Lock()

    def stop_connection(self, application_id: str) -> None:
        """Stop one managed worker immediately (used by the admin actions)."""
        process = self.children.pop(application_id, None)
        if process is not None and process.is_alive():
            process.terminate()
            process.join(timeout=5)

    async def reconcile(self, *, start_missing: bool = False, application_id: str | None = None):
        async with self._lock:
            async with AsyncSessionLocal() as session:
                rows = (await session.execute(select(FeishuApplication, ApiKey).join(ApiKey, ApiKey.id == FeishuApplication.api_key_id))).all()
                all_apps = {str(app.id): app for app, _ in rows}
                wanted = {str(app.id): (app, key) for app, key in rows if app.desired_state == 'running' and key.is_active}
                for app_id, process in list(self.children.items()):
                    if app_id not in wanted or not process.is_alive():
                        if process.is_alive(): process.terminate(); process.join(timeout=5)
                        self.children.pop(app_id, None)
                        if app_id in wanted and all_apps[app_id].desired_state == 'running':
                            all_apps[app_id].connection_status = 'error'
                            all_apps[app_id].last_error = 'Feishu long-connection process exited unexpectedly'
                for app_id, app in all_apps.items():
                    if app.desired_state == 'stopped' and app_id not in self.children:
                        app.connection_status = 'stopped'
                for app_id, (app, key) in wanted.items():
                    process = self.children.get(app_id)
                    # With automatic restore disabled, a persisted desired
                    # state must never be presented as a live connection after
                    # the API process has restarted.  It is only a preference
                    # to restore if the environment switch is later enabled.
                    if process is None and not start_missing and app.connection_status in {'running', 'starting'}:
                        app.connection_status, app.last_error = 'stopped', None
                    if process is None and start_missing and (application_id is None or application_id == app_id):
                        try:
                            config = BotConfig(app.app_id, decrypt_secret(app.app_secret_ciphertext), key.key_value or '', app_id)
                            if not config.platform_api_key: raise RuntimeError('bound API Key value is unavailable')
                            process = multiprocessing.Process(target=run_connection, args=(config,), daemon=True, name=f'feishu-{app.name}')
                            process.start(); self.children[app_id] = process; app.connection_status, app.last_error = 'running', None
                        except Exception as exc: app.connection_status, app.last_error = 'error', str(exc)
                    app.last_heartbeat_at = datetime.now(UTC)
                await session.commit()
    async def run(self, *, auto_start_on_service_boot: bool = False):
        while True:
            try: await self.reconcile(start_missing=auto_start_on_service_boot)
            except Exception: LOG.exception('Feishu reconciliation failed')
            await asyncio.sleep(POLL_SECONDS)
    def shutdown(self):
        for application_id in list(self.children):
            self.stop_connection(application_id)

def main():
    logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'), format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    auto_start = os.getenv("FEISHU_AUTO_START_ON_SERVICE_BOOT", "false").strip().lower() in {"1", "true", "yes", "on"}
    asyncio.run(Manager().run(auto_start_on_service_boot=auto_start))
if __name__ == '__main__': main()
