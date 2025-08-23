
import sys
import traceback
import threading
import time
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox

class SafeAIChatWorker(QThread):
    """Thread-safe AI chat worker with crash protection"""
    response_ready = Signal(str)
    error_occurred = Signal(str)
    finished_signal = Signal()
    
    def __init__(self, message, service=None):
        super().__init__()
        self.message = message
        self.service = service
        self._running = True
    
    def run(self):
        """Run AI chat with crash protection"""
        try:
            if not self._running:
                return
                
            # Add timeout protection
            def timeout_handler():
                if self._running:
                    self.error_occurred.emit("AI response timeout - please try again")
                    self.finished_signal.emit()
            
            # Set up timeout
            timer = threading.Timer(30.0, timeout_handler)
            timer.start()
            
            try:
                if self.service and hasattr(self.service, 'xai_chat'):
                    response = self.service.xai_chat(self.message)
                    if self._running:
                        self.response_ready.emit(response or "No response received")
                else:
                    self.error_occurred.emit("AI service not available")
            finally:
                timer.cancel()
                
        except Exception as e:
            if self._running:
                error_msg = f"AI Chat Error: {str(e)}"
                print(f"AI Chat Error: {e}")
                traceback.print_exc()
                self.error_occurred.emit(error_msg)
        finally:
            self.finished_signal.emit()
    
    def stop(self):
        """Safely stop the worker"""
        self._running = False
        self.quit()
        self.wait(1000)  # Wait up to 1 second

class SafeVoiceChatWorker(QThread):
    """Thread-safe voice chat worker with crash protection"""
    voice_heard = Signal(str)
    error_occurred = Signal(str)
    finished_signal = Signal()
    
    def __init__(self):
        super().__init__()
        self._running = True
    
    def run(self):
        """Run voice recognition with crash protection"""
        try:
            import speech_recognition as sr
            
            recognizer = sr.Recognizer()
            
            # Adjust for ambient noise
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                
            with sr.Microphone() as source:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
                
            if self._running:
                try:
                    query = recognizer.recognize_google(audio)
                    self.voice_heard.emit(query)
                except sr.UnknownValueError:
                    self.error_occurred.emit("Could not understand audio")
                except sr.RequestError as e:
                    self.error_occurred.emit(f"Speech service error: {e}")
                    
        except ImportError:
            self.error_occurred.emit("Speech recognition not available")
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

def safe_ai_chat(message, service=None, parent_widget=None):
    """Safe AI chat function with error handling"""
    try:
        worker = SafeAIChatWorker(message, service)
        
        def on_response(response):
            if parent_widget and hasattr(parent_widget, 'chat_display'):
                parent_widget.chat_display.append(f"AI: {response}")
        
        def on_error(error):
            if parent_widget and hasattr(parent_widget, 'chat_display'):
                parent_widget.chat_display.append(f"❌ {error}")
            if parent_widget:
                QMessageBox.warning(parent_widget, "AI Chat Error", error)
        
        def on_finished():
            worker.deleteLater()
        
        worker.response_ready.connect(on_response)
        worker.error_occurred.connect(on_error)
        worker.finished_signal.connect(on_finished)
        
        worker.start()
        return worker
        
    except Exception as e:
        error_msg = f"Failed to start AI chat: {str(e)}"
        print(error_msg)
        traceback.print_exc()
        if parent_widget:
            QMessageBox.critical(parent_widget, "AI Chat Error", error_msg)
        return None

def safe_voice_chat(parent_widget=None):
    """Safe voice chat function with error handling"""
    try:
        worker = SafeVoiceChatWorker()
        
        def on_voice_heard(text):
            if parent_widget and hasattr(parent_widget, 'chat_input'):
                parent_widget.chat_input.setText(text)
                parent_widget.chat_display.append(f"You (Voice): {text}")
        
        def on_error(error):
            if parent_widget and hasattr(parent_widget, 'chat_display'):
                parent_widget.chat_display.append(f"❌ {error}")
        
        def on_finished():
            worker.deleteLater()
        
        worker.voice_heard.connect(on_voice_heard)
        worker.error_occurred.connect(on_error)
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

print("✅ Safe AI chat utilities loaded")
