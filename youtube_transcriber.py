import os
from pathlib import Path
from typing import Optional
import ffmpeg
import whisper
from pytube import YouTube
from tqdm import tqdm

class VideoDownloader:
    """Handles downloading YouTube videos and extracting audio."""
    
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def download_audio(self, url: str) -> Optional[Path]:
        """
        Downloads audio from YouTube video and converts to WAV format.
        
        Args:
            url: YouTube video URL
            
        Returns:
            Path to converted audio file or None if failed
        """
        try:
            # Configure YouTube with custom headers
            yt = YouTube(
                url,
                on_progress_callback=self._progress_callback,
                use_oauth=False
            )
            
            # Try different stream selection approaches
            audio_stream = None
            
            try:
                # First attempt: Try getting audio-only stream with highest quality
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                
                # Second attempt: Try getting any audio stream
                if not audio_stream:
                    audio_stream = yt.streams.filter(only_audio=True).first()
                
                # Third attempt: Try getting the lowest quality stream that has audio
                if not audio_stream:
                    audio_stream = yt.streams.filter(progressive=True).order_by('resolution').first()
                
            except Exception as stream_error:
                print(f"Stream selection error: {stream_error}")
                # Final attempt: Try getting any available stream
                audio_stream = yt.streams.first()
            
            if not audio_stream:
                raise ValueError("No suitable audio stream found")
                
            # Download audio
            print(f"Downloading audio using stream: {audio_stream.itag}")
            audio_file = audio_stream.download(output_path=str(self.output_dir))
            downloaded_path = Path(audio_file)
            
            # Convert to WAV format for better compatibility with Whisper
            wav_path = downloaded_path.with_suffix('.wav')
            print("Converting audio format...")
            self._convert_to_wav(downloaded_path, wav_path)
            
            # Remove the original file
            downloaded_path.unlink()
            
            return wav_path
            
        except Exception as e:
            print(f"Error downloading/converting video: {str(e)}")
            if "HTTP Error 400" in str(e):
                print("This might be due to regional restrictions or age verification requirements.")
            elif "HTTP Error 403" in str(e):
                print("Access forbidden. This might be due to YouTube's security measures.")
            print("\nTroubleshooting steps:")
            print("1. Try updating pytube: pip install --upgrade pytube")
            print("2. Check if the video is available in your region")
            print("3. Check if the video requires age verification")
            print("4. Try using a different video URL")
            return None
    
    def _convert_to_wav(self, input_path: Path, output_path: Path) -> None:
        """Convert audio file to WAV format using ffmpeg."""
        try:
            stream = ffmpeg.input(str(input_path))
            stream = ffmpeg.output(stream, str(output_path))
            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
        except ffmpeg.Error as e:
            print(f"Error converting audio: {str(e.stderr.decode())}")
            raise
    
    @staticmethod
    def _progress_callback(stream, chunk, bytes_remaining):
        """Callback to show download progress."""
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        print(f"\rDownload Progress: {percentage:.1f}%", end="")

class Transcriber:
    """Handles audio transcription using Whisper."""
    
    def __init__(self, model_size: str = "base"):
        self.model = whisper.load_model(model_size)
    
    def transcribe(self, audio_path: Path, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Transcribes audio file to text.
        
        Args:
            audio_path: Path to audio file
            output_path: Optional path to save transcript
            
        Returns:
            Transcript text or None if failed
        """
        try:
            print("\nTranscribing audio...")
            result = self.model.transcribe(str(audio_path))
            transcript = result["text"]
            
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(transcript)
                print(f"Transcript saved to: {output_path}")
            
            return transcript
            
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return None

def main():
    """Main function to run the transcription process."""
    try:
        # Read URL from url.txt
        with open('url.txt', 'r') as file:
            url = file.read().strip()
            
        if not url:
            print("Error: url.txt is empty")
            return
            
        print(f"Processing URL: {url}")
        
        # Initialize components
        downloader = VideoDownloader()
        transcriber = Transcriber()
        
        # Download audio
        audio_path = downloader.download_audio(url)
        if not audio_path:
            return
        
        # Create output path for transcript
        transcript_path = audio_path.with_suffix(".txt")
        
        # Transcribe audio
        transcript = transcriber.transcribe(audio_path, transcript_path)
        if transcript:
            print("\nTranscription completed successfully!")
            print("\nTranscript preview:")
            print(transcript[:500] + "..." if len(transcript) > 500 else transcript)
            
    except FileNotFoundError:
        print("Error: url.txt file not found. Please create a url.txt file with the YouTube URL.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 