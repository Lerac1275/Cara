from dataclasses import dataclass


@dataclass
class BotState:
    is_active: bool = True


bot_state = BotState()
