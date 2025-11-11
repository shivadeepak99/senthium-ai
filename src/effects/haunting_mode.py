"""
Haunting Mode - Psychological deterrent for intruders

Spooky effects to scare away unauthorized users! 👻💀
"""

import logging
import random
import time
from pathlib import Path
from typing import Optional, List
import platform

logger = logging.getLogger(__name__)

# Check for TTS availability
TTS_AVAILABLE = False
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ pyttsx3 not available - TTS whispers disabled")

# Check for screen effects (Windows only for now)
SCREEN_EFFECTS_AVAILABLE = False
if platform.system() == 'Windows':
    try:
        import ctypes
        SCREEN_EFFECTS_AVAILABLE = True
    except:
        pass


class HauntingMode:
    """
    Spooky psychological deterrent for intruders.
    
    Features:
    - 🔊 TTS whispers ("I see you...")
    - 🎬 Screen flash effects
    - 📢 Escalating audio warnings
    - 💀 Creepy messages
    
    Your PC becomes a haunted house! 👻
    """
    
    # Whisper messages (escalating creepiness)
    WHISPERS_LEVEL_1 = [
        "I see you...",
        "Who are you?",
        "You shouldn't be here...",
        "This is not your computer...",
        "Smile for the camera...",
    ]
    
    WHISPERS_LEVEL_2 = [
        "The owner has been notified...",
        "Security systems activated...",
        "Your face has been captured...",
        "Photos are being sent...",
        "Law enforcement will be contacted...",
    ]
    
    WHISPERS_LEVEL_3 = [
        "System lockdown in 3... 2... 1...",
        "All access denied...",
        "Intruder alert! Intruder alert!",
        "Emergency protocols activated...",
        "You have 5 seconds to leave...",
    ]
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize haunting mode.
        
        Args:
            config: Configuration dict with haunting settings
        """
        self.config = config or {}
        self.enabled = self.config.get('enabled', False)
        self.effects = self.config.get('effects', [
            'tts_whisper',
            'screen_flash',
            'creepy_message'
        ])
        self.escalation_enabled = self.config.get('escalation', True)
        
        # Initialize TTS engine
        self.tts_engine = None
        if TTS_AVAILABLE and 'tts_whisper' in self.effects:
            try:
                self.tts_engine = pyttsx3.init()
                # Set voice properties (slower, deeper = creepier!)
                self.tts_engine.setProperty('rate', 120)  # Slower speech
                self.tts_engine.setProperty('volume', 0.9)  # Loud
                
                # Try to set a deeper voice (male voice if available)
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Prefer male voice (usually voices[0] on Windows)
                    self.tts_engine.setProperty('voice', voices[0].id)
                
                logger.info("👻 TTS engine initialized for haunting mode")
            except Exception as e:
                logger.warning(f"⚠️ Failed to init TTS: {e}")
                self.tts_engine = None
        
        # Escalation level tracking
        self.escalation_level = 1
        self.last_haunt_time = 0
        
        logger.info(f"👻 Haunting mode initialized (enabled: {self.enabled})")
    
    def haunt(self, duration_seconds: float = 0, force_level: Optional[int] = None) -> dict:
        """
        Execute haunting effects on intruder!
        
        Args:
            duration_seconds: How long intruder has been detected (for escalation)
            force_level: Force specific escalation level (1-3), or None for auto
        
        Returns:
            Dict with effects executed
        """
        if not self.enabled:
            return {"haunted": False, "reason": "Haunting mode disabled"}
        
        # Determine escalation level
        if force_level:
            level = force_level
        elif self.escalation_enabled:
            # Auto-escalate based on duration
            if duration_seconds < 5:
                level = 1  # Soft warning
            elif duration_seconds < 15:
                level = 2  # Serious warning
            else:
                level = 3  # FULL HAUNT!
        else:
            level = 1  # No escalation
        
        effects_executed = []
        
        # Execute enabled effects
        if 'tts_whisper' in self.effects:
            whisper_result = self._speak_whisper(level)
            if whisper_result:
                effects_executed.append('tts_whisper')
        
        if 'screen_flash' in self.effects:
            flash_result = self._screen_flash(level)
            if flash_result:
                effects_executed.append('screen_flash')
        
        if 'creepy_message' in self.effects:
            message_result = self._show_creepy_message(level)
            if message_result:
                effects_executed.append('creepy_message')
        
        self.last_haunt_time = time.time()
        
        logger.info(f"👻 Haunting executed! Level: {level}, Effects: {effects_executed}")
        
        return {
            "haunted": True,
            "level": level,
            "effects": effects_executed,
            "timestamp": self.last_haunt_time
        }
    
    def _speak_whisper(self, level: int = 1) -> bool:
        """
        Speak a creepy whisper using TTS.
        
        Args:
            level: Escalation level (1-3)
        
        Returns:
            True if whisper spoken successfully
        """
        if not self.tts_engine:
            return False
        
        try:
            # Select whisper based on level
            if level == 1:
                messages = self.WHISPERS_LEVEL_1
            elif level == 2:
                messages = self.WHISPERS_LEVEL_2
            else:
                messages = self.WHISPERS_LEVEL_3
            
            # Pick random message
            whisper = random.choice(messages)
            
            logger.debug(f"👻 Speaking whisper (L{level}): {whisper}")
            
            # Speak it!
            self.tts_engine.say(whisper)
            self.tts_engine.runAndWait()
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ TTS whisper failed: {e}")
            return False
    
    def _screen_flash(self, level: int = 1) -> bool:
        """
        Flash the screen (red pulsing border effect).
        
        Args:
            level: Escalation level (1-3)
        
        Returns:
            True if flash executed
        """
        if not SCREEN_EFFECTS_AVAILABLE:
            return False
        
        try:
            # Number of flashes based on level
            flash_count = level
            
            # TODO: Implement screen flash using tkinter or similar
            # For now, just log it
            logger.debug(f"👻 Screen flash x{flash_count} (L{level})")
            
            # Placeholder - would need GUI implementation
            # Could use tkinter to create fullscreen red border window
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Screen flash failed: {e}")
            return False
    
    def _show_creepy_message(self, level: int = 1) -> bool:
        """
        Show creepy on-screen message.
        
        Args:
            level: Escalation level (1-3)
        
        Returns:
            True if message shown
        """
        try:
            # Select message based on level
            if level == 1:
                title = "⚠️ Unauthorized Access"
                message = "This computer is protected.\nYour presence has been detected and recorded."
            elif level == 2:
                title = "🚨 SECURITY ALERT"
                message = "INTRUDER DETECTED!\n\nYour face has been captured.\nThe owner has been notified.\n\nLeave immediately."
            else:
                title = "🔴 SYSTEM LOCKDOWN"
                message = "CRITICAL SECURITY BREACH!\n\nAll activities are being recorded.\nLaw enforcement has been contacted.\n\nYou have been warned."
            
            logger.debug(f"👻 Showing creepy message (L{level}): {title}")
            
            # Show message box (platform-specific)
            if platform.system() == 'Windows':
                import ctypes
                # MB_OK | MB_ICONWARNING | MB_SYSTEMMODAL
                icon_type = 0x00000030 if level == 1 else 0x00000010  # Warning or Error
                ctypes.windll.user32.MessageBoxW(0, message, title, icon_type | 0x00001000)
            else:
                # Fallback: print to console
                print(f"\n{'='*50}\n{title}\n{'-'*50}\n{message}\n{'='*50}\n")
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Creepy message failed: {e}")
            return False
    
    def stop(self):
        """Stop TTS engine and cleanup."""
        if self.tts_engine:
            try:
                self.tts_engine.stop()
            except:
                pass
    
    def get_stats(self) -> dict:
        """Get haunting mode statistics."""
        return {
            "enabled": self.enabled,
            "tts_available": TTS_AVAILABLE and self.tts_engine is not None,
            "screen_effects_available": SCREEN_EFFECTS_AVAILABLE,
            "effects": self.effects,
            "escalation_enabled": self.escalation_enabled,
            "last_haunt_time": self.last_haunt_time
        }


# Quick convenience function
def haunt_intruder(duration: float = 0, config: Optional[dict] = None) -> dict:
    """Quick haunt an intruder!"""
    haunter = HauntingMode(config)
    return haunter.haunt(duration)
