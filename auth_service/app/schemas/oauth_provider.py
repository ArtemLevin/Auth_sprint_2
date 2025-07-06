from pydantic import AnyUrl, BaseModel, Field, SecretStr


class OAuthProvider(BaseModel):
    client_id: str
    client_secret: SecretStr
    authorize_url: AnyUrl
    token_url: AnyUrl
    api_base_url: AnyUrl
    callback_url: AnyUrl
    client_kwargs: dict = Field(default_factory=lambda: {"scope": "openid profile email"})