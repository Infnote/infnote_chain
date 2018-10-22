import string

from enum import Enum
from json import JSONDecoder, JSONEncoder, JSONDecodeError
from random import choices
from dataclasses import dataclass, field


@dataclass
class Message:
    class Type(Enum):
        BROADCAST = 'broadcast'
        QUESTION = 'question'
        ANSWER = 'answer'
        ERROR = 'error'

    content: dict = None
    type: Type = Type.QUESTION
    identifier: str = field(default_factory=lambda: ''.join(choices(string.digits + string.ascii_letters, k=10)))

    @classmethod
    def load(cls, json_string):
        try:
            json = JSONDecoder().decode(json_string)
            msg = Message()
            msg.identifier = json['identifier']
            msg.type = cls.Type(json['type'])
            msg.content = json['content']
            return msg
        except (KeyError, ValueError, JSONDecodeError):
            return None

    def dump(self) -> str:
        json = {
            'identifier': self.identifier,
            'type': self.type.value,
            'content': self.content
        }
        return JSONEncoder(ensure_ascii=False, separators=(',', ':')).encode(json)

    def __repr__(self):
        return f'<Message: {self.identifier} - {self.type}>'
