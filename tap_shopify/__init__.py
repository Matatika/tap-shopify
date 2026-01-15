"""Default init."""

from collections import UserDict


# important that this doesn't subclass dict directly to ensure json.dumps calls do not
# expose the contents
class hiddendict(UserDict):
    """Dict-like object that does not expose contents when serialised."""

    def __repr__(self):
        return "***"
