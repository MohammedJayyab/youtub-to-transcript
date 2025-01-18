from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from pathlib import Path
from typing import Optional
import re
import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

class TranscriptFetcher:
    """Handles fetching transcripts from YouTube videos."""
    
    def __init__(self, output_dir: str = "transcripts"):
        """Initialize the TranscriptFetcher with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in .env file")
    
    def get_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',
            r'youtu\.be/([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("Invalid YouTube URL format")
    
    def fetch_transcript(self, url: str, output_path: Optional[Path] = None) -> Optional[tuple[str, str]]:
        """
        Fetch transcript from YouTube video.
        
        Args:
            url: YouTube video URL
            output_path: Optional path to save transcript
            
        Returns:
            Tuple of (transcript text, language code) or None if failed
        """
        try:
            video_id = self.get_video_id(url)
            print(f"Fetching transcript for video ID: {video_id}")
            
            # Get available transcripts
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            try:
                # Try to get manual transcripts first
                transcript = transcript_list.find_manually_created_transcript()
            except:
                try:
                    # Fall back to generated transcripts
                    transcript = transcript_list.find_generated_transcript()
                except:
                    # Finally, try to get any available transcript
                    transcript = transcript_list.find_transcript(['en','ar', 'es', 'fr', 'de', 'it'])
            
            # Get the transcript data and language
            transcript_data = transcript.fetch()
            language = transcript.language_code
            
            # Format transcript
            formatter = TextFormatter()
            formatted_transcript = formatter.format_transcript(transcript_data)
            
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"Language: {language}\n\n")
                    f.write(formatted_transcript)
                print(f"Transcript saved to: {output_path}")
            
            return formatted_transcript, language
            
        except Exception as e:
            print(f"Error fetching transcript: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Check if the video has closed captions available")
            print("2. Check if the video is available in your region")
            print("3. Try using a different video URL")
            return None
    
    def summarize_text(self, text: str, language: str) -> dict:
        """
        Summarize text using Deepseek API.
        
        Args:
            text: Text to summarize
            language: Language code of the transcript
            
        Returns:
            Dictionary containing summary components
        """
        headers = {
            'Authorization': f'Bearer {self.deepseek_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Adjust prompt based on language
        prompt = f"""Please analyze the following transcript in {language} and provide:
1. A brief abstract (2-3 sentences)
2. Key concepts (bullet points)
3. Category of the topic
4. A detailed summary (4-5 paragraphs)

Please provide the analysis in the same language as the transcript ({language}).

Format your response exactly like this:
ABSTRACT:
(your abstract here)

KEY CONCEPTS:
• (concept 1)
• (concept 2)
...

CATEGORY:
(category here)

SUMMARY:
(your detailed summary here)

Transcript:
{text}
"""
        
        data = {
            'model': 'deepseek-chat',
            'messages': [
                {
                    'role': 'user', 
                    'content': prompt
                }
            ],
            'temperature': 0.7,
            'max_tokens': 4000
        }

        try:
            response = requests.post(
                'https://api.deepseek.com/v1/chat/completions',
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            sections = content.split('\n\n')
            response_dict = {}
            
            for section in sections:
                if section.startswith('ABSTRACT:'):
                    response_dict['abstract'] = section.replace('ABSTRACT:', '').strip()
                elif section.startswith('KEY CONCEPTS:'):
                    concepts = [line.strip('• ').strip() for line in section.split('\n')[1:] if line.strip()]
                    response_dict['key_concepts'] = concepts
                elif section.startswith('CATEGORY:'):
                    response_dict['category'] = section.replace('CATEGORY:', '').strip()
                elif section.startswith('SUMMARY:'):
                    response_dict['summary'] = section.replace('SUMMARY:', '').strip()
            
            return response_dict
            
        except Exception as e:
            print(f"Error in summarization: {str(e)}")
            if hasattr(e, 'response'):
                print(f"API Response: {e.response.text}")
            return None

    def process_transcript(self, transcript_data: tuple[str, str], summary_path: Path) -> None:
        """Process transcript and save summary."""
        transcript, language = transcript_data
        print(f"\nDetected language: {language}")
        print("\nGenerating summary using Deepseek AI...")
        
        summary_data = self.summarize_text(transcript, language)
        
        if summary_data:
            try:
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(f"=== TRANSCRIPT ANALYSIS (Language: {language}) ===\n\n")
                    f.write("ABSTRACT:\n")
                    f.write(summary_data.get('abstract', 'Not available'))
                    f.write("\n\nKEY CONCEPTS:\n")
                    for concept in summary_data.get('key_concepts', []):
                        f.write(f"• {concept}\n")
                    f.write(f"\nCATEGORY:\n{summary_data.get('category', 'Not available')}\n")
                    f.write("\nDETAILED SUMMARY:\n")
                    f.write(summary_data.get('summary', 'Not available'))
                
                print("\nAnalysis Results:")
                print("\nAbstract:")
                print(summary_data.get('abstract', 'Not available'))
                print("\nKey Concepts:")
                for concept in summary_data.get('key_concepts', []):
                    print(f"• {concept}")
                print(f"\nCategory: {summary_data.get('category', 'Not available')}")
                print("\nDetailed summary has been saved to the output file.")
                
            except Exception as e:
                print(f"Error saving summary: {str(e)}")
        else:
            print("Failed to generate summary.")

def main():
    """Main function to run the transcript fetching process."""
    try:
        with open('url.txt', 'r') as file:
            url = file.read().strip()
            
        if not url:
            print("Error: url.txt is empty")
            return
            
        print(f"Processing URL: {url}")
        
        fetcher = TranscriptFetcher()
        
        video_id = fetcher.get_video_id(url)
        transcript_path = fetcher.output_dir / f"{video_id}_transcript.txt"
        summary_path = fetcher.output_dir / f"{video_id}_analysis.txt"
        
        transcript_data = fetcher.fetch_transcript(url, transcript_path)
        if transcript_data:
            print("\nTranscript fetching completed successfully!")
            fetcher.process_transcript(transcript_data, summary_path)
            
    except FileNotFoundError:
        print("Error: url.txt file not found. Please create a url.txt file with the YouTube URL.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 