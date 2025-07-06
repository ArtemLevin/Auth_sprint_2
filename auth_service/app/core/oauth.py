from authlib.integrations.starlette_client import OAuth

from app.settings import settings

oauth = OAuth()

for name, cfg in settings.oauth_providers.items():
    oauth.register(
        name=name,
        client_id=cfg.client_id,
        client_secret=cfg.client_secret.get_secret_value(),
        access_token_url=cfg.token_url,
        authorize_url=cfg.authorize_url,
        api_base_url=cfg.api_base_url,
        client_kwargs=cfg.client_kwargs,
    )