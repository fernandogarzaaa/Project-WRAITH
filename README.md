# Project WRAITH (Web-Roaming Artificial Intelligence & Training Hub)

WRAITH is an autonomous, self-evolving, cryptographic swarm ecosystem designed to run locally on consumer hardware (e.g., RTX 2060).

It combines three radical concepts into a single circadian daemon:

1. **Poltergeist (The Action Layer):** A headless browser swarm that roams the internet as a digital decoy, poisoning surveillance trackers while simultaneously scraping high-value data, reasoning patterns, and code.
2. **Babel (The Communication Layer):** An LLM-to-LLM compression protocol. WRAITH agents communicate using dense symbolic hashes instead of English, reducing token consumption by 80% and eliminating hallucinated misunderstandings.
3. **Somnus (The Evolution Layer):** A nocturnal fine-tuning loop. While you sleep, WRAITH compiles the day's scraped data into an Alpaca-style dataset and runs an automated Unsloth LoRA fine-tune on your local LLM. It wakes up smarter every day.

## Architecture
- `orchestrator/god_node.py`: The master circadian daemon.
- `poltergeist/scraper_swarm.py`: The headless Playwright decoy and scraper.
- `babel/protocol.py`: The AI-to-AI symbolic hash parser.
- `somnus/evolution_loop.py`: The automated Unsloth fine-tuning pipeline.

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Install Playwright browsers: `playwright install chromium`
4. Run the daemon: `python orchestrator/god_node.py`

*Note: WRAITH requires a local LLM backend (like Ollama or llama.cpp) running on localhost.*

## License
MIT
