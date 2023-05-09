import os
import unittest
from unittest.mock import patch
from flask_httpauth import HTTPTokenAuth
import jwt

auth = HTTPTokenAuth(scheme="Bearer")

PROFILE_TYPE_PRIVATE = "private"
PROFILE_TYPE_COMMERCIAL = "commercial"
PROFILE_TYPE_PRIVATE_ATTRIBUTES = "private-attributes"

OIDC_CLIENT_ID_DIGID = os.getenv("OIDC_CLIENT_ID_DIGID", "digid")
OIDC_CLIENT_ID_EHERKENNING = os.getenv("OIDC_CLIENT_ID_EHERKENNING", "eherkenning")
OIDC_CLIENT_ID_YIVI = os.getenv("OIDC_CLIENT_ID_YIVI", "yivi")
OIDC_JWKS_URL = os.getenv("OIDC_JWKS_URL", "")

TOKEN_ID_ATTRIBUTE_EHERKENNING = "urn:etoegang:1.9:EntityConcernedID:KvKnr"

# Op 1.13 met ketenmachtiging
EH_ATTR_INTERMEDIATE_PRIMARY_ID = "urn:etoegang:core:LegalSubjectID"
EH_ATTR_INTERMEDIATE_SECONDARY_ID = "urn:etoegang:1.9:IntermediateEntityID:KvKnr"

# 1.13 inlog zonder ketenmachtiging:
EH_ATTR_PRIMARY_ID = "urn:etoegang:core:LegalSubjectID"

# < 1.13 id
EH_ATTR_PRIMARY_ID_LEGACY = "urn:etoegang:1.9:EntityConcernedID:KvKnr"

TOKEN_ID_ATTRIBUTE_DIGID = "sub"
TOKEN_ID_ATTRIBUTE_YIVI = "sub"

ProfileTypeByClientId = {
    OIDC_CLIENT_ID_DIGID: PROFILE_TYPE_PRIVATE,
    OIDC_CLIENT_ID_EHERKENNING: PROFILE_TYPE_COMMERCIAL,
    OIDC_CLIENT_ID_YIVI: PROFILE_TYPE_PRIVATE_ATTRIBUTES,
}

ClientIdByProfileType = {
    PROFILE_TYPE_PRIVATE: OIDC_CLIENT_ID_DIGID,
    PROFILE_TYPE_COMMERCIAL: OIDC_CLIENT_ID_EHERKENNING,
    PROFILE_TYPE_PRIVATE_ATTRIBUTES: OIDC_CLIENT_ID_YIVI,
}


def get_eherkenning_id_attribute(tokenData):
    if (
        EH_ATTR_INTERMEDIATE_PRIMARY_ID in tokenData
        and EH_ATTR_INTERMEDIATE_SECONDARY_ID in tokenData
    ):
        return EH_ATTR_INTERMEDIATE_PRIMARY_ID

    if EH_ATTR_PRIMARY_ID in tokenData:
        return EH_ATTR_PRIMARY_ID

    # Attr Prior to 1.13
    return EH_ATTR_PRIMARY_ID_LEGACY


TokenAttributeByProfileType = {
    PROFILE_TYPE_PRIVATE: lambda tokenData: TOKEN_ID_ATTRIBUTE_DIGID,
    PROFILE_TYPE_COMMERCIAL: get_eherkenning_id_attribute,
    PROFILE_TYPE_PRIVATE_ATTRIBUTES: lambda tokenData: TOKEN_ID_ATTRIBUTE_YIVI,
}

login_required = auth.login_required


class AuthError(Exception):
    pass


AuthException = [jwt.PyJWTError, AuthError]


def is_auth_exception(error):
    for err in AuthException:
        if isinstance(error, err):
            return True
    return False


def get_profile_type(token_data):
    return ProfileTypeByClientId[token_data["aud"]]


def get_client_id(profile_type):
    return ClientIdByProfileType[profile_type]


def get_id_token_attribute_by_profile_type(token_data):
    profile_type = get_profile_type(token_data)
    return TokenAttributeByProfileType[profile_type](token_data)


def get_profile_id(token_data):
    id_attribute = get_id_token_attribute_by_profile_type(token_data)
    return token_data[id_attribute]


def get_verified_token_data(token):
    jwks_client = jwt.PyJWKClient(OIDC_JWKS_URL)
    signing_key = jwks_client.get_signing_key_from_jwt(token)

    audience = [
        get_client_id(PROFILE_TYPE_PRIVATE),
        get_client_id(PROFILE_TYPE_COMMERCIAL),
    ]

    token_data = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience=audience,
    )

    return token_data


def get_user_profile_from_token(token):
    token_data = get_verified_token_data(token)

    profile_type = get_profile_type(token_data)
    profile_id = get_profile_id(token_data)

    return {"id": profile_id, "type": profile_type}


@auth.verify_token
def verify_token(token):
    if not token:
        raise AuthError("Token not found")
    return get_user_profile_from_token(token)


def get_current_user():
    return auth.current_user()


class FlaskServerTestCase(unittest.TestCase):
    TEST_BSN = "111222333"
    TEST_KVK = "333222111"

    app = None
    client = None

    rsa_private_key_test = {
        "p": "8b-T1GJux6AGYWz1FLaXdTVkXsVQ2_oNFMs-gJBRXMpDT_1g3LlrjtEd_Y2-HuaDbEAoS8ccGlC9IIjbYcunQBqD1whl3tiGFswzDk2DUaJjXZnPAjYHWUHa1cl3tkDEo9uzWJ0h201QH7bG0Ls2Jl1IPOtSzPcNHBO0iWg_WH0",
        "kty": "RSA",
        "q": "3GtC1fHI297LqVHGN9btnf5nt7pT_TVWltYxio3DJvrNsAHiAHmwr87FNheSLcaBgUgqGYcGnQrvnW4Ly_c5Sb_xEMwigp5TcpjPYjHZGv5ML5Rf8yEZJAjiFJ6RuUWRHOZ0qRJSnFuVDdj1xfH4dUkZGfJ2vl9DMm6mRhGk6As",
        "d": "mYegF_YD30wsYPrk241n7vsEk7tnCqqFPd25_5XRwHeo33qSiQMgDKvpHjthoWMCMmY_e9V_af-Ht_eX6uM0T7mMrQCpAvjeOrcRd1vMuMxVoMOTmVrn_wZNEFaYTs4zTmy3-fYjQiB1le1kOGO6t03FXeQFTWgJQTTVOCrHAIILrOSj0HqtQomzsw9J7MLXd2eRuKDZydRSbJEhPg3NUzHeJjbuKJg6aVlj-gSaQ1s79vteIjm3pwItAkEsSP5R4LCrlxPPdIW4ghemGwi2jIfJhxzW7v3Q0sI6MYZ10FwkiUh9W1IUbUADQIT7Jf7EZ1yt_u8s7c9dvJ-NotHi4Q",
        "e": "AQAB",
        "use": "sig",
        "kid": "8YN3pNDUUyho-tQB25afq8DKCrxt2V-bS6W9gRk0cgk",
        "qi": "fAfkX1oqy_U-vU_eaCgEHYvZZxS7r1pSZpqipFitJdHayqlZEVwddmQZZ30IX3tHk3NRfjm6zy6FCXrVXVleAOkPyJpPXVsK_GiUufh28u5hPncs3KaFU0tTQ373Vd7IgOF7IhshyImR6UAXQiLSPLaEFQdte5DRL4kMkgwYHF8",
        "dp": "EyIpjh64S95zgtR_1ULaW_F83y9YxgBVdrbbXIuPlPuBNlyEhRO72pLcf8vvJzzxW-j8B3tb0w1e2qtaSbQ3qZAvrR5CCdAzVKyWweQKp7Rljuv0gWVLUZovusn2Spt3tMxXtoTBQD0vQUNTGwQmNgUeCYxKgmRvSjCZEmMI2HU",
        "alg": "RS256",
        "dq": "2xIAK4NTjrOw12hfCcCkChOAIisertsEZIYeVwbunx9Gr1gvtyk7YoCvoUNsFfLlZAjFTvnUqODlpiJptx7P4WzTu04oPon9hjg6Ze4FSb7VGbTuaEbNJfNuP_AaBXoO8BpceG2tjZm4Wzr3ivUja-5q9E73ld44ezdeKuX-cGE",
        "n": "0CXtOrsyIGkhhJ_sHzGbyK9U6sug4HdjdSNaq-FVbFFO_OeAaS8NvzM7DJXkZvmvZ7HNIPdlRk0-TCELmbOGK1RlddQZA_iic9DePydxloNJIWmUVI5GK1T84PxhjnMfBAD3SWPdTZ0zG1IubAjUJT4nwl0uVdzp0-LixbmKPQU87dqA1jt7ZuC73M55oZAyi1e2fzvgdxWyM7-NyvkZqwG2eGoDQ3SNb0rArlHTgdsLf1YsGPxn1wN3bSjhrq6af4fCnB5UVRb-r3g4NN_VJxBOc2xGDDoOgaPW9XW-BhSefc2hqRjTwtjaGiZFLdEuZdcq_mUB-AHc0YYD3_4VXw",
    }

    rsa_public_key_test = {
        "keys": [
            {
                "kty": "RSA",
                "e": "AQAB",
                "use": "sig",
                "kid": "8YN3pNDUUyho-tQB25afq8DKCrxt2V-bS6W9gRk0cgk",
                "alg": "RS256",
                "n": "0CXtOrsyIGkhhJ_sHzGbyK9U6sug4HdjdSNaq-FVbFFO_OeAaS8NvzM7DJXkZvmvZ7HNIPdlRk0-TCELmbOGK1RlddQZA_iic9DePydxloNJIWmUVI5GK1T84PxhjnMfBAD3SWPdTZ0zG1IubAjUJT4nwl0uVdzp0-LixbmKPQU87dqA1jt7ZuC73M55oZAyi1e2fzvgdxWyM7-NyvkZqwG2eGoDQ3SNb0rArlHTgdsLf1YsGPxn1wN3bSjhrq6af4fCnB5UVRb-r3g4NN_VJxBOc2xGDDoOgaPW9XW-BhSefc2hqRjTwtjaGiZFLdEuZdcq_mUB-AHc0YYD3_4VXw",
            }
        ]
    }

    def get_test_app_client(self, app):
        app.testing = True
        return app.test_client()

    def setUp(self):
        self.client = self.get_test_app_client(self.app)
        self.maxDiff = None

    def get_user_id(self, profile_type):
        if profile_type == PROFILE_TYPE_COMMERCIAL:
            return self.TEST_KVK

        return self.TEST_BSN

    def get_token_header_value(self, profile_type):
        token_data = {
            "aud": get_client_id(profile_type),
        }

        id_attribute = get_id_token_attribute_by_profile_type(token_data)

        token_data[id_attribute] = self.get_user_id(profile_type)

        key = jwt.api_jwk.PyJWK.from_dict(
            self.rsa_private_key_test, algorithm="RS256"
        ).key

        token = jwt.encode(
            token_data,
            key,
            algorithm="RS256",
            headers={"kid": self.rsa_private_key_test["kid"]},
        )

        return f"Bearer {token}"

    def add_authorization_headers(self, profile_type, headers=None):
        if headers is None:
            headers = {}

        headers["Authorization"] = self.get_token_header_value(profile_type)

        return headers

    def get_secure(self, location, profile_type=PROFILE_TYPE_PRIVATE, headers=None):
        with patch.object(jwt.PyJWKClient, "fetch_data") as fetch_data_mock:
            fetch_data_mock.return_value = self.rsa_public_key_test
            return self.client.get(
                location,
                headers=self.add_authorization_headers(profile_type, headers=headers),
            )

    def post_secure(
        self, location, profile_type=PROFILE_TYPE_PRIVATE, headers=None, json=None
    ):
        with patch.object(jwt.PyJWKClient, "fetch_data") as fetch_data_mock:
            fetch_data_mock.return_value = self.rsa_public_key_test
            headers = self.add_authorization_headers(profile_type, headers=headers)
            return self.client.post(
                location,
                headers=headers,
                json=json,
            )
