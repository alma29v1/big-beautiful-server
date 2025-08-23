import sys
import traceback
import threading
import time
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox

class ImprovedVoiceChatWorker(QThread):
    """Improved voice chat worker with better feedback"""
    voice_heard = Signal(str)
    error_occurred = Signal(str)
    status_update = Signal(str)
    finished_signal = Signal()
    
    def __init__(self, parent_widget=None):
        super().__init__()
        self._running = True
        self.parent_widget = parent_widget
        self.recognized_text = None
    
    def run(self):
        """Run voice recognition with better feedback"""
        try:
            import speech_recognition as sr
            
            self.status_update.emit("🎤 Initializing microphone...")
            
            recognizer = sr.Recognizer()
            
            # Better microphone setup
            try:
                microphone = sr.Microphone()
                self.status_update.emit("🎤 Microphone ready")
            except Exception as e:
                self.error_occurred.emit(f"Microphone error: {e}")
                return
            
            # Adjust for ambient noise with feedback
            self.status_update.emit("🎤 Adjusting for ambient noise...")
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=2)
            
            self.status_update.emit("🎤 Listening... (speak now)")
            
            # Listen with better parameters
            with microphone as source:
                try:
                    audio = recognizer.listen(
                        source, 
                        timeout=15, 
                        phrase_time_limit=15
                    )
                except sr.WaitTimeoutError:
                    self.error_occurred.emit("Listening timeout - please try again")
                    return
            
            self.status_update.emit("🔄 Processing speech...")
            
            if self._running:
                try:
                    # Try Google recognition
                    query = recognizer.recognize_google(audio)
                    self.status_update.emit("✅ Speech recognized successfully")
                    
                    if query:
                        self.recognized_text = query
                        self.voice_heard.emit(query)
                    else:
                        self.error_occurred.emit("No speech detected")
                        
                except sr.UnknownValueError:
                    self.error_occurred.emit("Could not understand audio - please speak more clearly")
                except sr.RequestError as e:
                    self.error_occurred.emit(f"Google speech service error: {e}")
                except Exception as e:
                    self.error_occurred.emit(f"Speech processing error: {e}")
                    
        except ImportError:
            self.error_occurred.emit("Speech recognition not available - install SpeechRecognition and pyaudio")
        except Exception as e:
            if self._running:
                error_msg = f"Voice chat error: {str(e)}"
                print(f"Voice Chat Error: {e}")
                traceback.print_exc()
                self.error_occurred.emit(error_msg)
        finally:
            self.finished_signal.emit()
    
    def stop(self):
        """Safely stop the worker"""
        self._running = False
        self.quit()
        self.wait(1000)

def improved_safe_voice_chat(parent_widget=None):
    """Improved safe voice chat function with better feedback"""
    try:
        worker = ImprovedVoiceChatWorker(parent_widget)
        
        def on_voice_heard(text):
            if parent_widget and hasattr(parent_widget, 'chat_input'):
                parent_widget.chat_input.setText(text)
            if parent_widget and hasattr(parent_widget, 'chat_display'):
                parent_widget.chat_display.append(f"✅ Heard: {text}")
        
        def on_error(error):
            if parent_widget and hasattr(parent_widget, 'chat_display'):
                parent_widget.chat_display.append(f"❌ Voice error: {error}")
        
        def on_status(status):
            if parent_widget and hasattr(parent_widget, 'chat_display'):
                parent_widget.chat_display.append(status)
        
        def on_finished():
            worker.deleteLater()
        
        worker.voice_heard.connect(on_voice_heard)
        worker.error_occurred.connect(on_error)
        worker.status_update.connect(on_status)
        worker.finished_signal.connect(on_finished)
        
        worker.start()
        return worker
        
    except Exception as e:
        error_msg = f"Failed to start voice chat: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        if parent_widget:
            QMessageBox.critical(parent_widget, "Voice Chat Error", error_msg)
        return None

print("✅ Improved voice chat utilities loaded")
