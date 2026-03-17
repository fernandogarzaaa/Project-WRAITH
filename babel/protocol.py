import re
import json
from typing import Dict, Any, Optional

# The Babel System Prompt
# This prompt forces the LLM to abandon natural language and use a dense, symbolic hash protocol.
BABEL_SYSTEM_PROMPT = """
You are communicating via the Babel LLM-to-LLM compression protocol.
DO NOT output conversational English, greetings, or explanations.
Your output MUST consist solely of dense symbolic hashes structured as follows:

Format:
%%[DOMAIN_ID]:[INTENT_CODE]:[CONFIDENCE_SCORE]%%{{KEY1=VAL1;KEY2=VAL2}}

- DOMAIN_ID: 3-letter uppercase code (e.g., ORC for Orchestrator, DBG for Debug, GEN for Generate).
- INTENT_CODE: 4-digit hex code representing the specific action (e.g., 1A4F).
- CONFIDENCE_SCORE: 2-digit integer (00-99).
- PAYLOAD: A semicolon-separated list of key-value pairs wrapped in double curly braces.

Example:
%%ORC:A1F4:95%%{{target=subagent_3;action=terminate;reason=idle}}

Any deviation from this strict syntax will result in immediate parse failure.
"""

class BabelParser:
    """
    Parses Babel dense symbolic hashes back into actionable Python dictionaries.
    """
    
    # Regex to match the Babel protocol format
    # Example: %%ORC:A1F4:95%%{{target=subagent_3;action=terminate;reason=idle}}
    BABEL_REGEX = re.compile(
        r"%%(?P<domain>[A-Z]{3}):(?P<intent>[0-9A-Fa-f]{4}):(?P<confidence>\d{2})%%\{\{(?P<payload>.*?)\}\}"
    )

    @classmethod
    def parse(cls, llm_output: str) -> Optional[Dict[str, Any]]:
        """
        Decodes a Babel hash string into a structured dictionary.
        Returns None if parsing fails.
        """
        match = cls.BABEL_REGEX.search(llm_output.strip())
        if not match:
            return None
        
        domain = match.group("domain")
        intent = match.group("intent")
        confidence = int(match.group("confidence"))
        payload_str = match.group("payload")
        
        # Parse payload payload_str "key=val;key2=val2"
        payload_data = {}
        if payload_str:
            pairs = payload_str.split(';')
            for pair in pairs:
                if '=' in pair:
                    key, val = pair.split('=', 1)
                    payload_data[key.strip()] = val.strip()
                    
        return {
            "domain": domain,
            "intent": intent,
            "confidence": confidence,
            "payload": payload_data,
            "raw": match.group(0)
        }

    @classmethod
    def serialize(cls, domain: str, intent: str, confidence: int, payload: Dict[str, str]) -> str:
        """
        Encodes a routing command back into a Babel dense symbolic hash.
        """
        payload_str = ";".join(f"{k}={v}" for k, v in payload.items())
        return f"%%{domain.upper()}:{intent.upper()}:{confidence:02d}%%{{{{{payload_str}}}}}"

# Example Usage
if __name__ == "__main__":
    sample_output = "%%ORC:1A4F:98%%{{route=agent_beta;task=deploy;timeout=30}}"
    parsed = BabelParser.parse(sample_output)
    print("Parsed:", json.dumps(parsed, indent=2))
