from typing import Optional

from ecdsa.curves import NIST256p
from ecdsa.keys import SigningKey, VerifyingKey, BadSignatureError
from ecdsa.util import sigdecode_der, sigencode_der

from base58 import b58encode, b58decode
from hashlib import sha256


class Key:
    def __init__(self, public_key: str = None, private_key: str = None):
        self.__public_key = None
        self.__private_key = None

        if private_key is not None:
            self.__private_key = SigningKey.from_string(
                b58decode(private_key),
                curve=NIST256p
            )
            self.__public_key = self.__private_key.get_verifying_key()

        if public_key is not None:
            self.__public_key = VerifyingKey.from_string(
                b58decode(public_key)[1:],
                curve=NIST256p
            )

        if public_key is None and private_key is None:
            self.__private_key = SigningKey.generate(curve=NIST256p)
            self.__public_key = self.__private_key.get_verifying_key()

    @property
    def can_sign(self) -> bool:
        return self.__private_key is not None

    @property
    def public_key(self) -> str:
        # VerifyKey from ecdsa does not have the prefix byte (0x04)
        # we decided to use '0x04 | x | y' public key format
        return b58encode(b'\x04' + self.__public_key.to_string()).decode('ascii')

    @property
    def private_key(self) -> Optional[str]:
        if self.__private_key is not None:
            return b58encode(self.__private_key.to_string()).decode('ascii')
        return None

    @property
    def raw_public_key(self) -> bytes:
        return b'\x04' + self.__public_key.to_string()

    @property
    def raw_private_key(self) -> Optional[bytes]:
        return self.__private_key.to_string()

    def sign(self, data: bytes):
        if self.can_sign:
            return self.__private_key.sign(
                data,
                hashfunc=sha256,
                sigencode=sigencode_der
            )
        return None

    def verify(self, signature: str, data: bytes):
        try:
            return self.__public_key.verify(
                b58decode(signature),
                data,
                hashfunc=sha256,
                sigdecode=sigdecode_der
            )
        except BadSignatureError:
            return False
