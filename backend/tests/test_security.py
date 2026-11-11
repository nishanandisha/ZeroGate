import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import Settings
from app.core.security import decode_token

KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
S = Settings(keycloak_issuer="http://idp/realms/zerogate", api_audience="zerogate-api")


def token(**over):
    now = int(time.time())
    claims = {"iss": S.keycloak_issuer, "aud": "zerogate-api", "iat": now, "exp": now + 300,
              "sub": "u1", "preferred_username": "alice", "groups": ["zg-admins"], **over}
    return jwt.encode(claims, KEY, algorithm="RS256")


def test_valid():
    assert decode_token(token(), S, KEY.public_key())["preferred_username"] == "alice"


@pytest.mark.parametrize("bad", [{"aud": "other"}, {"iss": "http://evil"}, {"exp": int(time.time()) - 120}])
def test_rejects(bad):
    with pytest.raises(jwt.PyJWTError):
        decode_token(token(**bad), S, KEY.public_key())


def test_clock_skew_tolerance():
    # issued 20s "in the future" (IdP clock ahead) is tolerated by the 30s leeway ...
    decode_token(token(iat=int(time.time()) + 20), S, KEY.public_key())
    # ... a token that expired 10 minutes ago is not
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token(exp=int(time.time()) - 600), S, KEY.public_key())


def test_wrong_key():
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(jwt.InvalidSignatureError):
        decode_token(token(), S, other.public_key())
