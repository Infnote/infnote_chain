import string

from enum import Enum
from json import JSONDecoder, JSONEncoder, JSONDecodeError
from random import choices
from dataclasses import dataclass


@dataclass
class Message:
    class Type(Enum):
        QUESTION = 'question'
        ANSWER = 'answer'
        ERROR = 'error'

    content: dict = None
    type: Type = Type.QUESTION
    identifer: str = ''.join(choices(string.digits + string.ascii_letters, k=10))

    @classmethod
    def load(cls, json_string):
        try:
            json = JSONDecoder().decode(json_string)
            msg = Message()
            msg.identifer = json['identifier']
            msg.type = cls.Type(json['type'])
            msg.content = json['content']
            return msg
        except (KeyError, ValueError, JSONDecodeError):
            return None

    def dump(self) -> str:
        json = {
            'identifier': self.identifer,
            'type': self.type.value,
            'content': self.content
        }
        return JSONEncoder(ensure_ascii=False, separators=(',', ':')).encode(json)
