"""Legacy Telegram adapter retained only as an explicit compatibility guard."""


def run_bot(base_dir=None):
    raise RuntimeError(
        "interface/telegram_bot.py is retired. Start KonstanceAI with launcher.py or START_KONSTANCE.cmd."
    )
