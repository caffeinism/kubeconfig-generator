from collections import namedtuple
from oic.oic import Client
from oic.oic.message import RegistrationResponse
from oic.oic.message import AccessTokenRequest, AccessTokenResponse
from oic.oauth2.message import OauthMessageFactory
from oic.utils.authn.client import CLIENT_AUTHN_METHOD

MessageTuple = namedtuple("MessageTuple", ["request_cls", "response_cls"])


class RawAccessTokenResponse(AccessTokenResponse):
    def __init__(self, *args, **kwargs):
        super(RawAccessTokenResponse, self).__init__(*args, **kwargs)
        self.raw_id_token = None

    def verify(self, **kwargs):
        if "id_token" in self:
            self.raw_id_token = self['id_token']
        return super(RawAccessTokenResponse, self).verify(**kwargs)


class WrappedMessageFactory(OauthMessageFactory):
    token_endpoint = MessageTuple(AccessTokenRequest, RawAccessTokenResponse)


def get_oidc_client(
    issuer,
    client_id,
    client_secret,
    redirect_uri,
):
    client = Client(
        client_id=client_id,
        client_authn_method=CLIENT_AUTHN_METHOD,
        message_factory=WrappedMessageFactory,
    )
    client.provider_config(issuer)
    client.store_registration_info(
        RegistrationResponse(
            client_id=client_id,
            client_secret=client_secret,
        )
    )
    client.redirect_uris = [redirect_uri]

    return client
