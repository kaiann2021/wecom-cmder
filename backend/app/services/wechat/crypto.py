"""企业微信消息加解密模块

根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
章节: 3.2 消息加解密 (Message Crypto)

迁移自: MoviePilot-2/app/modules/wechat/WXBizMsgCrypt3.py
"""

import base64
import hashlib
import logging
import random
import socket
import struct
import time
import xml.etree.ElementTree as ET
from typing import Tuple

from Crypto.Cipher import AES

logger = logging.getLogger(__name__)

# 错误码定义
WXBizMsgCrypt_OK = 0
WXBizMsgCrypt_ValidateSignature_Error = -40001
WXBizMsgCrypt_ParseXml_Error = -40002
WXBizMsgCrypt_ComputeSignature_Error = -40003
WXBizMsgCrypt_IllegalAesKey = -40004
WXBizMsgCrypt_ValidateCorpid_Error = -40005
WXBizMsgCrypt_EncryptAES_Error = -40006
WXBizMsgCrypt_DecryptAES_Error = -40007
WXBizMsgCrypt_IllegalBuffer = -40008


class WeChatCryptoException(Exception):
    """企业微信加解密异常"""

    pass


class SHA1:
    """计算企业微信的消息签名"""

    @staticmethod
    def get_sha1(token: str, timestamp: str, nonce: str, encrypt: str) -> Tuple[int, str]:
        """用SHA1算法生成安全签名

        Args:
            token: 票据
            timestamp: 时间戳
            nonce: 随机字符串
            encrypt: 密文

        Returns:
            Tuple[int, str]: (错误码, 签名)
        """
        try:
            sortlist = [token, timestamp, nonce, encrypt]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist).encode())
            return WXBizMsgCrypt_OK, sha.hexdigest()
        except Exception as e:
            logger.error(f"计算签名失败: {e}")
            return WXBizMsgCrypt_ComputeSignature_Error, None


class XMLParse:
    """提供提取消息格式中的密文及生成回复消息格式的接口"""

    AES_TEXT_RESPONSE_TEMPLATE = """<xml>
<Encrypt><![CDATA[%(msg_encrypt)s]]></Encrypt>
<MsgSignature><![CDATA[%(msg_signature)s]]></MsgSignature>
<TimeStamp>%(timestamp)s</TimeStamp>
<Nonce><![CDATA[%(nonce)s]]></Nonce>
</xml>"""

    @staticmethod
    def extract(xmltext: str) -> Tuple[int, str]:
        """提取出xml数据包中的加密消息

        Args:
            xmltext: 待提取的xml字符串

        Returns:
            Tuple[int, str]: (错误码, 加密消息)
        """
        try:
            xml_tree = ET.fromstring(xmltext)
            encrypt = xml_tree.find("Encrypt")
            return WXBizMsgCrypt_OK, encrypt.text
        except Exception as e:
            logger.error(f"解析XML失败: {e}")
            return WXBizMsgCrypt_ParseXml_Error, None

    def generate(self, encrypt: str, signature: str, timestamp: str, nonce: str) -> str:
        """生成xml消息

        Args:
            encrypt: 加密后的消息密文
            signature: 安全签名
            timestamp: 时间戳
            nonce: 随机字符串

        Returns:
            str: 生成的xml字符串
        """
        resp_dict = {
            "msg_encrypt": encrypt,
            "msg_signature": signature,
            "timestamp": timestamp,
            "nonce": nonce,
        }
        return self.AES_TEXT_RESPONSE_TEMPLATE % resp_dict


class PKCS7Encoder:
    """提供基于PKCS7算法的加解密接口"""

    block_size = 32

    def encode(self, text: bytes) -> bytes:
        """对需要加密的明文进行填充补位

        Args:
            text: 需要进行填充补位操作的明文

        Returns:
            bytes: 补齐明文字符串
        """
        text_length = len(text)
        amount_to_pad = self.block_size - (text_length % self.block_size)
        if amount_to_pad == 0:
            amount_to_pad = self.block_size
        pad = chr(amount_to_pad)
        return text + (pad * amount_to_pad).encode()

    @staticmethod
    def decode(decrypted: bytes) -> bytes:
        """删除解密后明文的补位字符

        Args:
            decrypted: 解密后的明文

        Returns:
            bytes: 删除补位字符后的明文
        """
        pad = decrypted[-1]
        if pad < 1 or pad > 32:
            pad = 0
        return decrypted[:-pad]


class Prpcrypt:
    """提供接收和推送给企业微信消息的加解密接口"""

    def __init__(self, key: bytes):
        self.key = key
        self.mode = AES.MODE_CBC

    def encrypt(self, text: str, receiveid: str) -> Tuple[int, bytes]:
        """对明文进行加密

        Args:
            text: 需要加密的明文
            receiveid: 接收者ID

        Returns:
            Tuple[int, bytes]: (错误码, 加密后的字符串)
        """
        try:
            text = text.encode()
            text = (
                self.get_random_str()
                + struct.pack("I", socket.htonl(len(text)))
                + text
                + receiveid.encode()
            )

            pkcs7 = PKCS7Encoder()
            text = pkcs7.encode(text)

            cryptor = AES.new(self.key, self.mode, self.key[:16])
            ciphertext = cryptor.encrypt(text)
            return WXBizMsgCrypt_OK, base64.b64encode(ciphertext)
        except Exception as e:
            logger.error(f"加密失败: {e}")
            return WXBizMsgCrypt_EncryptAES_Error, None

    def decrypt(self, text: str, receiveid: str) -> Tuple[int, bytes]:
        """对密文进行解密

        Args:
            text: 密文
            receiveid: 接收者ID

        Returns:
            Tuple[int, bytes]: (错误码, 解密后的明文)
        """
        try:
            cryptor = AES.new(self.key, self.mode, self.key[:16])
            plain_text = cryptor.decrypt(base64.b64decode(text))
        except Exception as e:
            logger.error(f"解密失败: {e}")
            return WXBizMsgCrypt_DecryptAES_Error, None

        try:
            pad = plain_text[-1]
            content = plain_text[16:-pad]
            xml_len = socket.ntohl(struct.unpack("I", content[:4])[0])
            xml_content = content[4 : xml_len + 4]
            from_receiveid = content[xml_len + 4 :]
        except Exception as e:
            logger.error(f"解析解密内容失败: {e}")
            return WXBizMsgCrypt_IllegalBuffer, None

        if from_receiveid.decode("utf8") != receiveid:
            return WXBizMsgCrypt_ValidateCorpid_Error, None

        return WXBizMsgCrypt_OK, xml_content

    @staticmethod
    def get_random_str() -> bytes:
        """随机生成16位字符串

        Returns:
            bytes: 16位字符串
        """
        return str(random.randint(1000000000000000, 9999999999999999)).encode()


class WeChatCrypto:
    """企业微信消息加解密类

    根据 plan.md: spec/01-核心功能/wecom-cmder/plan.md
    章节: 3.2.2 核心方法
    """

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        """初始化加解密器

        Args:
            token: 回调Token
            encoding_aes_key: 回调加密Key
            corp_id: 企业ID

        Raises:
            WeChatCryptoException: 当EncodingAESKey无效时
        """
        try:
            self.key = base64.b64decode(encoding_aes_key + "=")
            if len(self.key) != 32:
                raise ValueError("EncodingAESKey长度必须为43字符")
        except Exception as e:
            raise WeChatCryptoException(f"EncodingAESKey无效: {e}")

        self.token = token
        self.corp_id = corp_id

    def verify_url(
        self, msg_signature: str, timestamp: str, nonce: str, echo_str: str
    ) -> str:
        """验证URL（企业微信回调验证）

        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            echo_str: 加密的随机字符串

        Returns:
            str: 解密后的echostr

        Raises:
            WeChatCryptoException: 验证失败时
        """
        sha1 = SHA1()
        ret, signature = sha1.get_sha1(self.token, timestamp, nonce, echo_str)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException("计算签名失败")

        if signature != msg_signature:
            raise WeChatCryptoException("签名验证失败")

        pc = Prpcrypt(self.key)
        ret, reply_echo_str = pc.decrypt(echo_str, self.corp_id)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException(f"解密失败，错误码: {ret}")

        return reply_echo_str.decode("utf8")

    def decrypt_message(
        self, msg_signature: str, timestamp: str, nonce: str, encrypt_msg: str
    ) -> str:
        """解密消息

        Args:
            msg_signature: 消息签名
            timestamp: 时间戳
            nonce: 随机数
            encrypt_msg: 加密的消息（XML格式）

        Returns:
            str: 解密后的消息（XML格式）

        Raises:
            WeChatCryptoException: 解密失败时
        """
        xml_parse = XMLParse()
        ret, encrypt = xml_parse.extract(encrypt_msg)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException("提取加密消息失败")

        sha1 = SHA1()
        ret, signature = sha1.get_sha1(self.token, timestamp, nonce, encrypt)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException("计算签名失败")

        if signature != msg_signature:
            raise WeChatCryptoException("签名验证失败")

        pc = Prpcrypt(self.key)
        ret, xml_content = pc.decrypt(encrypt, self.corp_id)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException(f"解密失败，错误码: {ret}")

        return xml_content.decode("utf8")

    def encrypt_message(
        self, reply_msg: str, nonce: str, timestamp: str = None
    ) -> Tuple[str, str]:
        """加密消息

        Args:
            reply_msg: 待加密的消息（XML格式）
            nonce: 随机数
            timestamp: 时间戳（可选，默认使用当前时间）

        Returns:
            Tuple[str, str]: (加密后的XML消息, 消息签名)

        Raises:
            WeChatCryptoException: 加密失败时
        """
        pc = Prpcrypt(self.key)
        ret, encrypt = pc.encrypt(reply_msg, self.corp_id)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException("加密失败")

        encrypt = encrypt.decode("utf8")

        if timestamp is None:
            timestamp = str(int(time.time()))

        sha1 = SHA1()
        ret, signature = sha1.get_sha1(self.token, timestamp, nonce, encrypt)
        if ret != WXBizMsgCrypt_OK:
            raise WeChatCryptoException("计算签名失败")

        xml_parse = XMLParse()
        return xml_parse.generate(encrypt, signature, timestamp, nonce), signature
