# YouTube Transcript & Summary Tool

## Description
A Python tool that fetches YouTube video transcripts and generates AI-powered summaries. It supports multiple languages and can either use YouTube's built-in captions or generate transcripts using Whisper AI.

## Installation
1. Create a virtual environment:
   python -m venv venv
   source venv/Scripts/activate  # Windows
   source venv/bin/activate     # Linux/Mac

2. Install dependencies:
   pip install -r requirements.txt

3. Set up environment variables:
   Create a `.env` file and add your Deepseek API key:
   DEEPSEEK_API_KEY=your_api_key_here

## Usage
1. Create a `url.txt` file with your YouTube URL
2. Run one of the following scripts:

   For YouTube captions:
   python youtube_transcript_fetcher.py

   For audio transcription:
   python youtube_transcriber.py

## Features
- Fetches YouTube video transcripts using official captions
- Generates transcripts from video audio using Whisper AI
- Supports multiple languages
- Creates AI-powered summaries including:
  - Brief abstract
  - Key concepts
  - Topic categorization
  - Detailed summary
- Saves both transcripts and analysis to text files

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License.
