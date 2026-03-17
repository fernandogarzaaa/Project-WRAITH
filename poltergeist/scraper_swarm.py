import asyncio
import random
import os
from datetime import datetime
from playwright.async_api import async_playwright

# High-value target sites
SITES = [
    "https://en.wikipedia.org/wiki/Special:Random",
    "https://arxiv.org/list/cs/recent",
    "https://github.com/trending",
    "https://news.ycombinator.com/",
    "https://en.wikipedia.org/wiki/Quantum_computing"
]

DATA_DIR = r"D:\Project Wraith\data\raw"

async def scrape_site(browser, instance_id):
    """Worker function for a single headless browser instance."""
    context = await browser.new_context(
        user_agent=f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Decoy/{instance_id}"
    )
    page = await context.new_page()
    
    try:
        while True:
            target = random.choice(SITES)
            # Silently log in the background (can be redirected to a log file or /dev/null if run via pythonw)
            print(f"[Instance {instance_id}] Visiting {target}")
            
            try:
                await page.goto(target, wait_until="domcontentloaded", timeout=60000)
                
                # Extract main text content
                text_content = await page.evaluate("document.body.innerText")
                
                # Save to raw data directory with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                domain = target.split("//")[1].split("/")[0].replace(".", "_")
                filename = os.path.join(DATA_DIR, f"scraped_{domain}_{timestamp}_inst{instance_id}.txt")
                
                with open(filename, "w", encoding="utf-8") as f:
                    # Save a chunk of text to prevent massive disk usage over time
                    f.write(text_content[:100000])
                    
            except Exception as e:
                print(f"[Instance {instance_id}] Scrape error on {target}: {e}")
            
            # Random sleep between 15 and 90 seconds to simulate sporadic background activity
            sleep_time = random.uniform(15, 90)
            await asyncio.sleep(sleep_time)
            
    except asyncio.CancelledError:
        print(f"[Instance {instance_id}] Shutting down.")
    finally:
        await context.close()

async def main():
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("Starting Wraith Poltergeist Swarm (Background Decoy & Scraper)...")
    
    async with async_playwright() as p:
        # Launch a single headless Chromium instance
        browser = await p.chromium.launch(headless=True)
        
        # Spawn 3 concurrent independent browser contexts/pages
        tasks = []
        for i in range(3):
            tasks.append(asyncio.create_task(scrape_site(browser, i + 1)))
            # Stagger startup slightly
            await asyncio.sleep(random.uniform(2, 5))
        
        # Run indefinitely
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Swarm terminated.")