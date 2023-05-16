class ErrorsWithCodes(type):
    def __getattribute__(self, code):
        msg = super().__getattribute__(code)
        if code.startswith("__"):  # python system attributes like __class__
            return msg
        else:
            return "[{code}] {msg}".format(code=code, msg=msg)


class Warnings(metaclass=ErrorsWithCodes):
    # File system
    W2001 = "Could not clean/remove the temp directory at {dir}: {msg}."


class Errors(metaclass=ErrorsWithCodes):
    # API - Datastructure
    E0001 = (
        "Can't write to frozen dictionary. This is likely an internal "
        "error. Are you writing to a default function argument?"
    )
    E0002 = (
        "Can't write to frozen list. Maybe you're trying to modify a computed "
        "property or default function argument?"
    )

    # Workflow
    E1001 = "Can not execute command '{str_command}'. Do you have '{tool}' installed?"

    # File system
    E2001 = "The tar file pulled from the remote attempted an unsafe path " "traversal."
