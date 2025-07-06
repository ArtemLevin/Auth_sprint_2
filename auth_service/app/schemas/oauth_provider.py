from pydantic import AnyUrl, BaseModel, Field, SecretStr, HttpUrl

class OAuthProvider(BaseModel):
    client_id: str = "test_client_id"
    client_secret: SecretStr = SecretStr('test_client_secret')
    authorize_url: AnyUrl = "https://example.com/authorize"
    token_url: AnyUrl = "https://example.com/token"
    api_base_url: AnyUrl = "https://example.com/api"
    callback_url: AnyUrl = "https://example.com/callback"
    client_kwargs: dict = Field(default_factory=lambda: {"scope": "openid profile email"})