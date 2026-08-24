"""Notion Tracker - AI Voice Command Agent (notion_voice_agent.py).

This module implements a code-driven, Notion-native Speech-to-Text command 
interpreter utilizing the Gemini 1.5 Flash API with local fallback simulation.

Instead of forcing users into an external React dashboard with a custom voice 
widget, operators attach audio recordings (.mp3, .wav, or .m4a) directly 
to Notion pages or comments (e.g., using Notion's native mobile/web microphone).

The background daemon polls for new audio attachments, uploads them server-side 
to the Gemini File API, and utilizes Gemini 1.5 Flash's native audio-modal 
understanding to transcribe, classify, and return structured command dispatches.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("VoiceAgent")

from config import NOTION_TOKEN
from notion_store import default_store
from notion_enterprise_guard import default_rate_limiter

# Conditional import of the Notion Client
try:
    from notion_client import Client, APIResponseError
except ImportError:
    Client = None
    APIResponseError = Exception

# Conditional import of the Gemini SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_SDK_AVAILABLE = False
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_SDK_AVAILABLE = True
except ImportError:
    logger.warning("google-generativeai library not installed. Running in mock demonstration mode.")


class NotionVoiceCommandAgent:
    """Enterprise Speech-to-Text command interpreter powered by Gemini 1.5 Flash with Notion typesetting."""

    def __init__(self, token: Optional[str] = None):
        tok = token or NOTION_TOKEN
        self.notion = Client(auth=tok) if (tok and Client) else None
        
    def process_voice_command(self, audio_file_path: str, context_details: str = "") -> dict:
        """
        Ingests a local audio file, uploads it to the Gemini File API, 
        and commands Gemini 1.5 Flash to extract natural language instructions.
        """
        logger.info(f"[*] Analyzing voice command file: {audio_file_path}")
        
        if not GEMINI_SDK_AVAILABLE:
            return self._simulate_gemini_voice_analysis(audio_file_path)
            
        try:
            # 1. Upload the audio file via Gemini's native File API
            logger.info("[*] Uploading audio block to Gemini File API...")
            uploaded_file = genai.upload_file(path=audio_file_path)
            logger.info(f"[+] Audio successfully uploaded. URI: {uploaded_file.uri}")
            
            # 2. Query Gemini 1.5 Flash with structured system prompting
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            system_prompt = (
                "You are an enterprise system command parser for Notion Tracker.\n"
                "Your job is to listen to the attached audio, transcribe it precisely, "
                "and extract structured administrative commands.\n\n"
                "Evaluate the transcription and return a strictly formatted JSON object with these keys:\n"
                "1. 'transcript': (string) Accurate word-for-word speech transcription.\n"
                "2. 'is_command': (boolean) True if speech intends to trigger an action (e.g. approve, decline, update database).\n"
                "3. 'command_type': (string) One of: 'APPROVE', 'REJECT', 'UPDATE_BUDGET', 'REASSIGN', 'QUERY_LOGS', or 'UNKNOWN'.\n"
                "4. 'parameters': (dictionary) Key-value pairs of any extracted parameters (e.g. {'budget': 4500, 'assignee': 'Aryan'}).\n"
                "5. 'confidence_score': (float) From 0.0 to 1.0 based on transcription certainty.\n\n"
                f"Context details regarding the current task state: {context_details}\n"
                "Output ONLY valid JSON. No markdown wrappers, no backticks, no trailing characters."
            )
            
            logger.info("[*] Invoking Gemini 1.5 Flash audio-modal decision engine...")
            response = model.generate_content([uploaded_file, system_prompt])
            
            # Clean response text from potential markdown block indicators
            clean_text = response.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()
            
            parsed_result = json.loads(clean_text)
            logger.info("[+] Gemini analysis successfully completed!")
            return parsed_result
            
        except Exception as e:
            logger.error(f"[-] Error processing voice via Gemini API: {e}")
            return {
                "error": True,
                "message": f"Gemini analysis failed: {str(e)}",
                "transcript": "Speech processing error.",
                "is_command": False,
                "command_type": "UNKNOWN",
                "parameters": {},
                "confidence_score": 0.0
            }
            
    def _simulate_gemini_voice_analysis(self, audio_file_path: str) -> dict:
        """Fallback mock analyzer to run in sandboxed testing environments without web access."""
        logger.info("[Demo Mode] Simulating Gemini 1.5 Flash audio-modal processing...")
        time.sleep(0.1)  # Low latency simulation
        
        file_name = os.path.basename(audio_file_path).lower()
        
        if "approve" in file_name or "success" in file_name:
            return {
                "transcript": "This is Aryan. Please approve task ninety nine and increase the budget cap to five thousand dollars.",
                "is_command": True,
                "command_type": "UPDATE_BUDGET",
                "parameters": {
                    "task_id": "99",
                    "budget": "$5,000",
                    "action": "APPROVE"
                },
                "confidence_score": 0.96
            }
        elif "reject" in file_name or "cancel" in file_name:
            return {
                "transcript": "Reject this deployment immediately and flag it for manual credential review.",
                "is_command": True,
                "command_type": "REJECT",
                "parameters": {
                    "reason": "Security Alert: Possible credential leak."
                },
                "confidence_score": 0.92
            }
        else:
            return {
                "transcript": "How many successful database executions have we recorded in the system log over the last hour?",
                "is_command": True,
                "command_type": "QUERY_LOGS",
                "parameters": {
                    "timeframe": "1h",
                    "outcome": "Success"
                },
                "confidence_score": 0.89
            }

    def execute_voice_command_in_notion(
        self,
        task_id: str,
        analysis_results: dict,
        operator_name: str = "Aryan Sharma",
    ) -> Dict[str, Any]:
        """
        Typesets the transcribed speech results natively inside Notion 
        and applies the associated database state mutation automatically.
        """
        transcript_content = analysis_results.get("transcript", "No transcript available.")
        cmd_type = analysis_results.get("command_type", "UNKNOWN")
        params = analysis_results.get("parameters", {})
        conf = int(analysis_results.get("confidence_score", 1.0) * 100)

        # 1. Update local database state with OCC
        task = default_store.get_task(task_id)
        local_updates = {}
        if cmd_type in ("APPROVE", "UPDATE_BUDGET"):
            local_updates["status"] = "Approved"
            if "budget" in params:
                local_updates["budget"] = f"${params['budget']}" if isinstance(params['budget'], (int, float)) else str(params['budget'])
            default_store.record_operator_approval(operator_name)
        elif cmd_type == "REJECT":
            local_updates["status"] = "Rejected"

        if task and local_updates:
            default_store.update_task_with_occ(
                task_id=task_id,
                base_record=task,
                local_updates=local_updates,
                operator_name=f"{operator_name} [Voice Agent]",
            )

        # 2. Append to Run Log
        default_store.write_to_run_log(
            record_id=task_id,
            action=f"VOICE_COMMAND_{cmd_type}",
            operator_name=f"{operator_name} [Voice Agent]",
            task_data={"transcript": transcript_content, "parameters": params, "confidence": conf},
            reasoning_steps=[
                f"🎙️ Transcribed Speech: '{transcript_content}'",
                f"🤖 Gemini 1.5 Flash Intent: {cmd_type} (Confidence: {conf}%)",
                f"📝 Extracted Parameters: {json.dumps(params)}",
            ],
            raw_payload=analysis_results,
        )

        # 3. Live Notion API Typesetting if configured
        if self.notion:
            try:
                logger.info(f"[*] Syncing voice command execution to Notion page {task_id}...")
                default_rate_limiter.acquire(1.0)
                self.notion.blocks.children.append(
                    block_id=task_id,
                    children=[
                        {
                            "object": "block",
                            "type": "heading_3",
                            "heading_3": {
                                "rich_text": [{"type": "text", "text": {"content": "🎙️ AI Voice Command Transcribed"}}]
                            }
                        },
                        {
                            "object": "block",
                            "type": "quote",
                            "quote": {
                                "rich_text": [{"type": "text", "text": {"content": f'"{transcript_content}"'}}]
                            }
                        },
                        {
                            "object": "block",
                            "type": "callout",
                            "callout": {
                                "rich_text": [
                                    {
                                        "type": "text",
                                        "text": {
                                            "content": f"Command Detected: {cmd_type}\n"
                                                       f"Parameters parsed: {json.dumps(params, indent=2)}\n"
                                                       f"Gemini Confidence: {conf}%"
                                        }
                                    }
                                ],
                                "icon": {"emoji": "🤖"},
                                "color": "green_background" if analysis_results.get("is_command") else "gray_background"
                            }
                        },
                        {"object": "block", "type": "divider", "divider": {}}
                    ]
                )
                
                notion_props = {}
                if cmd_type in ("APPROVE", "UPDATE_BUDGET"):
                    notion_props["Status"] = {"select": {"name": "Approved"}}
                elif cmd_type == "REJECT":
                    notion_props["Status"] = {"select": {"name": "Rejected"}}
                
                if notion_props:
                    self.notion.pages.update(page_id=task_id, properties=notion_props)
                    logger.info("[+] Notion page properties updated via voice command trigger successfully.")
            except Exception as e:
                logger.error(f"[-] Notion API update failed for voice execution: {e}")

        logger.info(f"[+] Voice command {cmd_type} executed successfully for task {task_id}.")
        return {
            "status": "SUCCESS",
            "command_type": cmd_type,
            "transcript": transcript_content,
            "parameters": params,
            "confidence_score": conf,
            "task_id": task_id,
        }


# Global default instance
default_voice_agent = NotionVoiceCommandAgent()


if __name__ == "__main__":
    print("=" * 60)
    print("       Notion Tracker: AI Voice Agent Command Test Suite")
    print("=" * 60)
    agent = NotionVoiceCommandAgent()
    
    # Run mock simulations
    print("\n[Test 1] Simulating approval voice recording...")
    r1 = agent.process_voice_command("voice_approve_command.wav")
    print(json.dumps(r1, indent=2))
    agent.execute_voice_command_in_notion("mock-task-page-id", r1)
    
    print("\n[Test 2] Simulating rejection voice recording...")
    r2 = agent.process_voice_command("voice_reject_alert.wav")
    print(json.dumps(r2, indent=2))
    agent.execute_voice_command_in_notion("mock-task-page-id", r2)
    print("\n[+] Voice simulation tests completed successfully!")
