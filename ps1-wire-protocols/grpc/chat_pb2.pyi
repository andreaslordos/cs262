from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ChatMessage(_message.Message):
    __slots__ = ["message", "sender", "to"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    message: str
    sender: str
    to: str
    def __init__(self, message: _Optional[str] = ..., to: _Optional[str] = ..., sender: _Optional[str] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class ListOfUsernames(_message.Message):
    __slots__ = ["usernames"]
    USERNAMES_FIELD_NUMBER: _ClassVar[int]
    usernames: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, usernames: _Optional[_Iterable[str]] = ...) -> None: ...

class Request(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class RequestResponse(_message.Message):
    __slots__ = ["success"]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    def __init__(self, success: bool = ...) -> None: ...

class SearchQuery(_message.Message):
    __slots__ = ["query"]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    query: str
    def __init__(self, query: _Optional[str] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ["name"]
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...
