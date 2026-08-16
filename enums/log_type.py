from enum import Enum

class LogType(Enum):
    LOGIN = 1
    SAVE = 2
    EDIT = 3
    DELETE = 4
    LOGOUT = 5
    REGISTER = 6
    LIKE = 7
    UNLIKE = 8
    PDF_EXPORT = 9
    AUTOCOMPLETE_QUERY = 10
    FOLLOW = 11
    UNFOLLOW = 12