from app.settings import settings
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='yandex',
    client_id=settings.yandex_client_id,
    client_secret=settings.yandex_client_secret.get_secret_value(),
    access_token_url='https://oauth.yandex.com/token',
    authorize_url='https://oauth.yandex.com/authorize',
    api_base_url='https://login.yandex.ru/info',
    client_kwargs={'scope': 'login:email'},
)