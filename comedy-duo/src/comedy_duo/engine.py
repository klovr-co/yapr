from pydantic_ai import Agent

from comedy_duo.models import (
    BotConfig,
    Commentary,
    CommentaryLine,
    EventTier,
    SessionEvent,
    Settings,
)


def build_commentary_prompt(
    event: SessionEvent,
    recent_history: list[tuple[str, str]],
) -> str:
    parts = [
        f"EVENT TYPE: {event.event_type}",
        f"EVENT TIER: {event.tier.value}",
        f"WHAT HAPPENED: {event.summary}",
    ]

    if recent_history:
        parts.append("\nRECENT COMMENTARY:")
        for name, text in recent_history[-5:]:
            parts.append(f"  {name}: {text}")

    parts.append("\nRespond with a short, punchy commentary line (1-2 sentences max).")
    return "\n".join(parts)


class CommentaryEngine:
    def __init__(self, bots: dict[str, BotConfig], settings: Settings):
        self.bots = bots
        self.settings = settings
        self._agents: dict[str, Agent] = {}

    def _get_agent(self, key: str) -> Agent:
        if key not in self._agents:
            bot = self.bots[key]
            system_prompt = (
                f"{bot.personality}\n\n"
                f"Example lines for tone reference:\n"
                + "\n".join(f"- {line}" for line in bot.example_lines)
            )
            self._agents[key] = Agent(
                self.settings.model_name,
                system_prompt=system_prompt,
            )
        return self._agents[key]

    async def _run_agent(self, bot_key: str, prompt: str) -> str:
        agent = self._get_agent(bot_key)
        result = await agent.run(prompt)
        return result.output

    async def generate(
        self,
        event: SessionEvent,
        recent_history: list[tuple[str, str]],
        force_duo: bool = False,
    ) -> Commentary:
        prompt = build_commentary_prompt(event, recent_history)

        is_duo = force_duo or event.tier == EventTier.HOT

        bot_keys = sorted(self.bots.keys())
        first_key = bot_keys[0]
        second_key = bot_keys[1] if len(bot_keys) > 1 else first_key

        first_text = await self._run_agent(first_key, prompt)
        lines = [CommentaryLine(bot_name=self.bots[first_key].name, text=first_text)]

        if is_duo and len(bot_keys) > 1:
            duo_prompt = (
                prompt
                + f'\n\n{self.bots[first_key].name} just said: "{first_text}"\n\nNow respond to them.'
            )
            second_text = await self._run_agent(second_key, duo_prompt)
            lines.append(CommentaryLine(bot_name=self.bots[second_key].name, text=second_text))

        return Commentary(lines=lines, is_duo=is_duo)
