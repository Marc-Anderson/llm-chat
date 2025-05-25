class ContentPresenter:
    """displays chat messages to the user"""

    def __init__(
        self,
        role: str,
        content: str,
        static: bool = True,
        excluded_from_history: bool = False,
    ):
        self.role = role
        self.content = content
        self.excluded = excluded_from_history
        if static:
            pass
        else:
            pass

    def update(self, content: str):
        self.content = content
        pass


class TerminalContentPresenter(ContentPresenter):
    """displays chat messages to the user in the terminal"""

    def __init__(
        self,
        role: str,
        content: str,
        static: bool = True,
        excluded_from_history: bool = False,
    ):
        super().__init__(role, content, static, excluded_from_history)
        if static:
            print(f"{role}: {self.content}")
        else:
            print(f"{role}: ", end="", flush=True)

    def update(self, content: str):
        self.content = content
        # Move cursor to start of line, clear it, re-print
        print("\r\033[K", end="", flush=True)
        print(f"{self.role}: {self.content}", end="", flush=True)
