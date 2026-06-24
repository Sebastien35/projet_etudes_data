import logging
import re
import shutil
import subprocess

logger = logging.getLogger("shared.claude_cli_service")

_CLAUDE_BIN = shutil.which("claude") or "/usr/local/bin/claude"

_VERDICT_COLORS = {
    "TRUE": "#34d399",
    "UNCERTAIN": "#fbbf24",
    "FALSE": "#f87171",
}

_PROMPT = """\
You are an expert fact-checker. Independently assess the claim below.
Before reasoning, use WebSearch to find current, reliable sources about the claim — do not rely solely on training data.

Your response MUST follow this exact format — no preamble, no extra text:
VERDICT: [write exactly TRUE, UNCERTAIN, or FALSE]

[2-3 sentences of reasoning. Cite the sources or evidence you found.]

CLAIM: {claim}\
"""


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _parse_output(raw: str) -> dict:
    output = _strip_ansi(raw).strip()
    verdict = "UNCERTAIN"
    reasoning = output

    lines = output.splitlines()
    verdict_idx = None
    for i, line in enumerate(lines):
        upper = line.strip().upper()
        if upper.startswith("VERDICT:"):
            raw_verdict = upper.removeprefix("VERDICT:").strip()
            if raw_verdict in _VERDICT_COLORS:
                verdict = raw_verdict
            verdict_idx = i
            break

    if verdict_idx is not None:
        reasoning_lines = [ln for ln in lines[verdict_idx + 1 :] if ln.strip()]
        reasoning = " ".join(reasoning_lines).strip() or output

    return {
        "verdict": verdict,
        "reasoning": reasoning,
        "color": _VERDICT_COLORS.get(verdict, "#7878a0"),
    }


class ClaudeCliService:
    def fact_check(self, claim: str) -> dict:
        prompt = _PROMPT.format(claim=claim)
        try:
            proc = subprocess.run(
                [_CLAUDE_BIN, "-p", prompt, "--allowedTools", "WebSearch"],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
                stdin=subprocess.DEVNULL,
            )
            output = proc.stdout.strip()
            if not output:
                logger.warning(
                    "Claude CLI empty output (stderr: %s)", proc.stderr[:200]
                )
                return {"verdict": "UNAVAILABLE", "reasoning": "", "color": "#7878a0"}
            return _parse_output(output)
        except FileNotFoundError:
            logger.error("Claude CLI not found at %s", _CLAUDE_BIN)
            return {
                "verdict": "UNAVAILABLE",
                "reasoning": "Claude CLI not found — see deployment docs.",
                "color": "#7878a0",
            }
        except subprocess.TimeoutExpired:
            logger.warning("Claude CLI timed out after 120s")
            return {
                "verdict": "TIMEOUT",
                "reasoning": "Claude did not respond in time.",
                "color": "#7878a0",
            }
        except Exception as e:
            logger.error("Claude CLI error: %s", e)
            return {"verdict": "ERROR", "reasoning": str(e), "color": "#7878a0"}


_instance = ClaudeCliService()


def get_claude_cli_service() -> ClaudeCliService:
    return _instance
