"""
CLI runner – useful for quick testing without launching Streamlit.

Usage:
    python main.py
"""

import asyncio
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from fan_companion import root_agent

load_dotenv()

WELCOME = """
╔══════════════════════════════════════════════════════════╗
║     ⚽  World Cup 2026 Fan Companion  ⚽                 ║
║     Powered by Gemini + MongoDB Atlas                    ║
║                                                          ║
║  Type your question and press Enter.                     ║
║  Type  quit  or  exit  to stop.                          ║
╚══════════════════════════════════════════════════════════╝
"""

EXAMPLE_PROMPTS = [
    "I want to see the USA vs Portugal match in Dallas. I'm flying from New York.",
    "What matches are playing in Los Angeles?",
    "Plan a trip to the Brazil vs Argentina match in Miami.",
]


async def chat_loop() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="worldcup_fan_companion",
        session_service=session_service,
    )
    session_id = "cli-session"

    print(WELCOME)
    print("Example prompts:")
    for i, p in enumerate(EXAMPLE_PROMPTS, 1):
        print(f"  {i}. {p}")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye! Enjoy the World Cup! ⚽")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye! Enjoy the World Cup! ⚽")
            break

        print("\nAgent: ", end="", flush=True)

        async for event in runner.run_async(
            user_id="cli_user",
            session_id=session_id,
            new_message=Content(role="user", parts=[Part(text=user_input)]),
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    print(event.content.parts[0].text)
        print()


if __name__ == "__main__":
    asyncio.run(chat_loop())
