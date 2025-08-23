#!/usr/bin/env python3
"""
Premium Voice System
High-quality text-to-speech with multiple voice options
"""

import asyncio
import os
import tempfile
import threading
import time
from typing import Optional, List, Dict
import json

class PremiumVoiceSystem:
    """Premium voice system with multiple high-quality voice options"""
    
    def __init__(self):
        self.current_voice = "en-US-AriaNeural"  # Default to high-quality neural voice
        self.voice_rate = 0  # Normal speed
        self.voice_volume = 100  # Full volume
        self.available_voices = {}
        self.voice_cache = {}
        self.load_available_voices()
    
    def load_available_voices(self):
        """Load available high-quality voices"""
        self.available_voices = {
            # Microsoft Edge TTS (High Quality Neural Voices)
            "en-US-AriaNeural": {
                "name": "Aria (Neural)",
                "description": "Professional female voice with natural intonation",
                "type": "edge-tts",
                "gender": "female",
                "quality": "neural"
            },
            "en-US-DavisNeural": {
                "name": "Davis (Neural)", 
                "description": "Professional male voice with clear articulation",
                "type": "edge-tts",
                "gender": "male",
                "quality": "neural"
            },
            "en-US-JennyNeural": {
                "name": "Jenny (Neural)",
                "description": "Friendly female voice with warm tone",
                "type": "edge-tts",
                "gender": "female",
                "quality": "neural"
            },
            "en-US-GuyNeural": {
                "name": "Guy (Neural)",
                "description": "Friendly male voice with approachable tone",
                "type": "edge-tts",
                "gender": "male",
                "quality": "neural"
            },
            "en-US-SaraNeural": {
                "name": "Sara (Neural)",
                "description": "Professional female voice with confident tone",
                "type": "edge-tts",
                "gender": "female",
                "quality": "neural"
            },
            "en-US-TonyNeural": {
                "name": "Tony (Neural)",
                "description": "Professional male voice with authoritative tone",
                "type": "edge-tts",
                "gender": "male",
                "quality": "neural"
            },
            # Google TTS (High Quality)
            "google-female": {
                "name": "Google Female",
                "description": "High-quality Google female voice",
                "type": "google-tts",
                "gender": "female",
                "quality": "high"
            },
            "google-male": {
                "name": "Google Male",
                "description": "High-quality Google male voice",
                "type": "google-tts",
                "gender": "male",
                "quality": "high"
            },
            # Local System Voices (Fallback)
            "system-default": {
                "name": "System Default",
                "description": "Your system's default voice",
                "type": "system",
                "gender": "unknown",
                "quality": "standard"
            }
        }
    
    def get_available_voices(self) -> Dict:
        """Get list of available voices"""
        return self.available_voices
    
    def set_voice(self, voice_id: str):
        """Set the current voice"""
        if voice_id in self.available_voices:
            self.current_voice = voice_id
            return True
        return False
    
    def set_rate(self, rate: int):
        """Set speech rate (-100 to 100)"""
        self.voice_rate = max(-100, min(100, rate))
    
    def set_volume(self, volume: int):
        """Set volume (0 to 100)"""
        self.voice_volume = max(0, min(100, volume))
    
    async def speak_edge_tts(self, text: str, voice_id: str) -> bool:
        """Speak using Microsoft Edge TTS (highest quality)"""
        try:
            import edge_tts
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            communicate = edge_tts.Communicate(text, voice_id, rate=f"{self.voice_rate:+d}%")
            await communicate.save(temp_path)
            
            # Play the audio
            self._play_audio_file(temp_path)
            
            # Clean up
            os.unlink(temp_path)
            return True
            
        except Exception as e:
            print(f"Edge TTS error: {e}")
            return False
    
    def speak_google_tts(self, text: str, voice_type: str) -> bool:
        """Speak using Google TTS"""
        try:
            from gtts import gTTS
            import pygame
            
            # Initialize pygame mixer
            pygame.mixer.init()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_path)
            
            # Play audio
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.quit()
            os.unlink(temp_path)
            return True
            
        except Exception as e:
            print(f"Google TTS error: {e}")
            return False
    
    def speak_system(self, text: str) -> bool:
        """Speak using system TTS"""
        try:
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Set properties
            engine.setProperty('rate', 200 + self.voice_rate)  # Base rate 200
            engine.setProperty('volume', self.voice_volume / 100.0)
            
            # Get available voices and set a good one
            voices = engine.getProperty('voices')
            if voices:
                # Try to find a good quality voice
                preferred_voices = ['Samantha', 'Victoria', 'Alex', 'Karen', 'Daniel']
                selected_voice = None
                
                for voice in voices:
                    voice_name = voice.name.lower()
                    for preferred in preferred_voices:
                        if preferred.lower() in voice_name:
                            selected_voice = voice
                            break
                    if selected_voice:
                        break
                
                if selected_voice:
                    engine.setProperty('voice', selected_voice.id)
            
            # Speak
            engine.say(text)
            engine.runAndWait()
            return True
            
        except Exception as e:
            print(f"System TTS error: {e}")
            return False
    
    def _play_audio_file(self, file_path: str):
        """Play audio file using pygame"""
        try:
            import pygame
            
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self.voice_volume / 100.0)
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            pygame.mixer.quit()
            
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    def speak(self, text: str) -> bool:
        """Speak text using the current voice"""
        if not text.strip():
            return False
        
        voice_info = self.available_voices.get(self.current_voice, {})
        voice_type = voice_info.get('type', 'system')
        
        print(f"🎤 Speaking with {voice_info.get('name', 'Unknown')}: {text[:50]}...")
        
        if voice_type == 'edge-tts':
            # Run async function in thread
            def run_edge_tts():
                asyncio.run(self.speak_edge_tts(text, self.current_voice))
            
            thread = threading.Thread(target=run_edge_tts)
            thread.start()
            thread.join()
            return True
            
        elif voice_type == 'google-tts':
            voice_gender = voice_info.get('gender', 'female')
            return self.speak_google_tts(text, voice_gender)
            
        else:  # system
            return self.speak_system(text)
    
    def speak_async(self, text: str):
        """Speak text asynchronously (non-blocking)"""
        thread = threading.Thread(target=self.speak, args=(text,))
        thread.daemon = True
        thread.start()
    
    def get_voice_info(self) -> str:
        """Get current voice information"""
        voice_info = self.available_voices.get(self.current_voice, {})
        return f"Current voice: {voice_info.get('name', 'Unknown')} ({voice_info.get('quality', 'standard')} quality)"
    
    def list_voices(self) -> str:
        """List all available voices"""
        result = "🎤 Available Premium Voices:\n\n"
        
        for voice_id, info in self.available_voices.items():
            current_marker = " (Current)" if voice_id == self.current_voice else ""
            result += f"• {info['name']}{current_marker}\n"
            result += f"  {info['description']}\n"
            result += f"  Quality: {info['quality']}\n\n"
        
        return result

# Global instance
premium_voice = PremiumVoiceSystem()

def speak_premium(text: str, voice_id: Optional[str] = None) -> bool:
    """Speak text with premium voice system"""
    if voice_id:
        premium_voice.set_voice(voice_id)
    return premium_voice.speak(text)

def speak_premium_async(text: str, voice_id: Optional[str] = None):
    """Speak text asynchronously with premium voice system"""
    if voice_id:
        premium_voice.set_voice(voice_id)
    premium_voice.speak_async(text)

def get_premium_voices() -> Dict:
    """Get available premium voices"""
    return premium_voice.get_available_voices()

def set_premium_voice(voice_id: str) -> bool:
    """Set premium voice"""
    return premium_voice.set_voice(voice_id)

def get_current_voice_info() -> str:
    """Get current voice information"""
    return premium_voice.get_voice_info()

def list_premium_voices() -> str:
    """List all premium voices"""
    return premium_voice.list_voices() 