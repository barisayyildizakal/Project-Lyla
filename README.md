# Lyla: AI-Driven Social Listening & Engagement Agent

Lyla is an experimental, AI-powered social media agent designed to analyze timeline trends and generate context-aware interactions. Built with a focus on data-driven content curation, it features a hybrid human-in-the-loop approval system via Telegram.

## Architecture & Key Features

* **Smart Social Listening:** Parses timeline data to identify contextual discussion points without relying on official API limits.
* **LLM Integration:** Utilizes the Google Gemini 1.5 Flash model for natural language understanding, sentiment analysis, and persona-driven response generation.
* **Hybrid Control Flow:** Can operate fully autonomously or route generated content to a Telegram interface for manual human review and approval.
* **Organic Pacing Engine:** Implements dynamic, randomized operational delays (randomized interval execution) to mimic natural human interaction patterns and ensure system stability.

## Tech Stack

* **Core Logic:** Python 3.x
* **Web Automation:** Playwright
* **AI/NLP Engine:** Google Generative AI (Gemini)
* **Orchestration:** pyTelegramBotAPI

## Disclaimer

This project was developed strictly for educational purposes, focusing on advanced web automation, LLM integration, and state management. It is designed to run locally and requires the user's own environment variables to function.
