import ssl

from ldap3 import Tls, Server, ALL, SYNC, SIMPLE, Connection
from pydantic_settings import BaseSettings, SettingsConfigDict


class LdapSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    LDAP_SERVER_DOMAIN: str
    LDAP_SERVER_PORT: int
    LDAP_USER: str
    LDAP_PASSWORD: str
    LDAP_SEARCH_BASE: str
    LDAP_USER_OUS: str
    LDAP_GROUP_OUS: str


def connect_ldap() -> Connection:
    ldap_settings = LdapSettings()
    tls_config = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
    server = Server(
        ldap_settings.LDAP_SERVER_DOMAIN,
        port=ldap_settings.LDAP_SERVER_PORT,
        tls=tls_config,
        get_info=ALL
    )
    return Connection(
        server,
        user=ldap_settings.LDAP_USER,
        password=ldap_settings.LDAP_PASSWORD,
        client_strategy=SYNC,
        authentication=SIMPLE
    )
