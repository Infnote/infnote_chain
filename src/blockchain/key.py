from typing import Optional

from ecdsa.curves import NIST256p
from ecdsa.keys import SigningKey, VerifyingKey, BadSignatureError
from ecdsa.util import sigdecode_der, sigencode_der, number_to_string, string_to_number

from base58 import b58encode, b58decode
from hashlib import sha256


class Key:
    @staticmethod
    def compress(public_key: bytes):
        """
        This method is avaliable for any curves.

        The result is a flag (0x02 y is even otherwise 0x03) connecting x with discarding y.

        :param public_key: public key bytes in uncompressed representation
        :return:
        """
        order = NIST256p.generator.order()
        pk_bytes = public_key[1:]
        pk_obj = VerifyingKey.from_string(pk_bytes, curve=NIST256p)
        point = pk_obj.pubkey.point

        flag = bytes([2 + (point.y() & 1)])
        x_bytes = number_to_string(point.x(), order)
        return flag + x_bytes

    @staticmethod
    def decompress(public_key: bytes):
        """
        This method is ONLY avaliable for NIST P-256/P-384/P-521,
        and not fit secp256k1(used by Bitcoin)

        Prefix(flag) 0x02 means y is even, 0x03 means y is odd,
        0x04 means the key is in uncompressed representation

        :param public_key: public key bytes string in compressed representation
        :return: public key bytes in uncompressed representation
        """
        order = NIST256p.generator.order()

        # Constant number
        # 2**256 - 2**224 + 2**192 + 2**96 - 1
        prime = 115792089210356248762697446949407573530086143415290314195533631308867097853951
        # (prime + 1) // 4
        p_ident = 28948022302589062190674361737351893382521535853822578548883407827216774463488
        b = 41058363725152142129326129780047268409114441015993725554835256314039467401291

        # Get x and flag from key
        flag = public_key[0] - 2
        x = string_to_number(public_key[1:])

        # powmod
        y = pow(x**3 - x*3 + b, p_ident, prime)
        if y % 2 != flag:
            y = prime - y

        y_bytes = number_to_string(y, order)
        return b'\x04' + public_key[1:] + y_bytes

    def __init__(self, public_key: str = None, private_key: str = None):
        """

        :param public_key: base58 encoded
        :param private_key: base58 encoded
        """
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
                self.decompress(b58decode(public_key))[1:],
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
        # return b58encode(b'\x04' + self.__public_key.to_string()).decode('ascii')
        return b58encode(self.compress(b'\x04' + self.__public_key.to_string())).decode('ascii')

    @property
    def private_key(self) -> Optional[str]:
        if self.__private_key is not None:
            return b58encode(self.__private_key.to_string()).decode('ascii')
        return None

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
