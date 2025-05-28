import sys
from pathlib import Path
import argparse

from agents import wait_agent

sys.path.append(str(Path(__file__).resolve().parent))
from agent_loader import load_agent

import logging
from app_logger import init_logging
logger:logging.Logger = init_logging()


def run_agent(agent_dir: str, input_file: str = None):
    agent = load_agent(agent_dir)
    print(f"[AgentLoader] Loaded agent: {agent.__class__.__name__}")
    
    agent.start_thread()

    # if hasattr(agent, "transcribe") and input_file:
    #     result = agent.transcribe(input_file)
    #     print(f"[STTAgent] Transcription result: {result}")
    # elif hasattr(agent, "generate"):
    #     result = agent.generate("What is AI?")
    #     print(f"[LLMAgent] Generation result: {result}")

    return agent


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start an AgentFlow agent.")
    parser.add_argument("--agent_dir", "-a", help="Path to the agent directory (e.g. agents/speech/stt_agent)")
    parser.add_argument("--input", "-i", help="Input file for agent (e.g. audio file for STT)")
    args = parser.parse_args()

    logger.debug(f"Agent directory: {args.agent_dir}")
    logger.debug(f"Input file: {args.input}")
    agent = run_agent(args.agent_dir, args.input)
    wait_agent(agent)
