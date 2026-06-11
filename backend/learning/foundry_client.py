"""
Microsoft Foundry client — Azure AI Project integration with local fallback.

Set AZURE_AI_PROJECT_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT for cloud models.
Falls back to GROQ_API_KEY / OPENAI_API_KEY via intelligence.llm when unset.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)

AZURE_AI_PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT", "")
AZURE_AI_MODEL_DEPLOYMENT = os.getenv("AZURE_AI_MODEL_DEPLOYMENT", "gpt-4o")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")
AZURE_RESOURCE_GROUP = os.getenv("AZURE_RESOURCE_GROUP", "")
AZURE_AI_PROJECT_NAME = os.getenv("AZURE_AI_PROJECT_NAME", "")


def is_foundry_configured() -> bool:
    return bool(AZURE_AI_PROJECT_ENDPOINT or (
        AZURE_SUBSCRIPTION_ID and AZURE_RESOURCE_GROUP and AZURE_AI_PROJECT_NAME
    ))


def get_foundry_status() -> dict[str, Any]:
    return {
        "configured": is_foundry_configured(),
        "project_endpoint": bool(AZURE_AI_PROJECT_ENDPOINT),
        "model_deployment": AZURE_AI_MODEL_DEPLOYMENT,
        "mode": "foundry" if is_foundry_configured() else "local_fallback",
    }


def _call_foundry(system_prompt: str, user_prompt: str, max_tokens: int = 500) -> Optional[str]:
    """Call Azure AI Foundry via azure-ai-projects when configured."""
    if not is_foundry_configured():
        return None
    try:
        from azure.identity import DefaultAzureCredential
        from azure.ai.projects import AIProjectClient

        if AZURE_AI_PROJECT_ENDPOINT:
            client = AIProjectClient(
                endpoint=AZURE_AI_PROJECT_ENDPOINT,
                credential=DefaultAzureCredential(),
            )
        else:
            client = AIProjectClient.from_connection_string(
                subscription_id=AZURE_SUBSCRIPTION_ID,
                resource_group_name=AZURE_RESOURCE_GROUP,
                project_name=AZURE_AI_PROJECT_NAME,
                credential=DefaultAzureCredential(),
            )

        agent = client.agents.create_agent(
            model=AZURE_AI_MODEL_DEPLOYMENT,
            name="learning-orchestrator",
            instructions=system_prompt,
        )
        thread = client.agents.create_thread()
        client.agents.create_message(thread_id=thread.id, role="user", content=user_prompt)
        run = client.agents.create_and_process_run(
            thread_id=thread.id,
            agent_id=agent.id,
        )
        if run.status == "completed":
            messages = client.agents.list_messages(thread_id=thread.id)
            for msg in reversed(list(messages)):
                if msg.role == "assistant" and msg.content:
                    for part in msg.content:
                        if hasattr(part, "text") and part.text:
                            return part.text.value
        logger.warning("Foundry run status: %s", run.status)
        return None
    except ImportError:
        logger.info("azure-ai-projects not installed; using local LLM fallback.")
        return None
    except Exception as e:
        logger.exception("Foundry call failed: %s", e)
        return None


def enrich_with_llm(
    system_prompt: str,
    user_prompt: str,
    fallback: str,
    max_tokens: int = 400,
) -> str:
    """Prefer Foundry, then Groq/OpenAI, then rule-based fallback."""
    result = _call_foundry(system_prompt, user_prompt, max_tokens)
    if result:
        return result

    try:
        from intelligence.llm import chat_completion
        result = chat_completion(user_prompt, system_prompt, max_tokens)
        if result:
            return result
    except Exception as e:
        logger.debug("Local LLM fallback failed: %s", e)

    return fallback
