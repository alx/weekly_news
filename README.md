# LinkAce to Hugo Weekly Digest

Automate your weekly link roundups: fetch new links from LinkAce, structure and summarize them with a top free LLM (via OpenRouter), review and polish the results, and export a Hugo-ready Markdown file.

---

## Features

- Fetches links from a specified LinkAce list (past 7 days)
- Summarizes and organizes links using OpenRouter's best free LLMs
- Interactive editor feedback loop
- Outputs Markdown with Hugo-compatible front matter

---

## Quick Start

1. **Clone & Install:**
   ```bash
   git clone https://github.com/alx/linkace-to-hugo-weekly.git
   cd linkace-to-hugo-weekly
   pip install -r requirements.txt
   ```

2. **Configure:**  
   Copy `.env.example` to `.env` and fill in your LinkAce and OpenRouter API keys, Hugo path, etc.

3. **Run:**
   ```bash
   python linkace_to_hugo.py
   ```

---

## Requirements

- Python 3.8+
- [LinkAce](https://www.linkace.org/) instance & API key
- [OpenRouter.ai](https://openrouter.ai/) API key
- Hugo site for publishing

---

## How it Works

- Fetches your latest links from LinkAce
- Uses an LLM to structure and summarize the content
- Lets you review and edit the draft
- Saves a Hugo-ready Markdown file in your content directory

---

## License

MIT License

---

*Inspired by automation and the joy of sharing knowledge.*
