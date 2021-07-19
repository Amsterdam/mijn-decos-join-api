from unittest.case import TestCase
from unittest.mock import patch

from cryptography.fernet import InvalidToken

from decosjoin.crypto import encrypt, decrypt


@patch("decosjoin.crypto.get_encrytion_key", lambda: "z4QXWk3bjwFST2HRRVidnn7Se8VFCaHscK39JfODzNs=")
class CryptoTest(TestCase):
    def test_encrypt_decrypt(self):
        value = "abcdefg"
        enc = encrypt(value)
        self.assertEqual(decrypt(enc), value)

    def test_encrypt_decrypt_bsn(self):
        value = "abcdefg"
        bsn = "12345678"
        enc = encrypt(value, bsn)
        self.assertEqual(decrypt(enc, bsn), value)
        pass

    def test_encrypt_decrypt_bsn_invalid(self):
        value = "abcdefg"
        bsn = "12345678"
        enc = encrypt(value, bsn)
        with self.assertRaises(InvalidToken):
            self.assertEqual(decrypt(enc, "2345"), value)

    def test_encrypt_bsn_decrypt_without_bsn(self):
        """ test encryption with bsn, but decryption without bsn verification. """
        value = "abcdefg"
        bsn = "12345678"
        enc = encrypt(value, bsn)
        self.assertEqual(decrypt(enc), value)

    def test_encrypt_without_bsn_decrypt_bsn(self):
        """ test encryption with bsn, but decryption without bsn verification. """
        value = "abcdefg"
        bsn = "12345678"
        enc = encrypt(value)
        with self.assertRaises(InvalidToken):
            self.assertEqual(decrypt(enc, bsn), value)
