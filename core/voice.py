import os
import sys
import re
import time
import tempfile
import asyncio
import threading
import speech_recognition as sr
try:
    import pythoncom
    import win32com.client
except ImportError:
    pythoncom = None
    win32com = None
from typing import Optional, Callable

try:
    import edge_tts
    import pygame
    _HAS_EDGE_TTS = True
except ImportError:
    _HAS_EDGE_TTS = False

# Ensure UTF-8 output handling on Windows consoles
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, 'reconfigure'):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


class VoiceEngine:
    def __init__(self, config=None):
        self.config = config or {}
        cfg = self.config.get('assistant', {})
        self.rate       = cfg.get('rate', 170)
        self.voice_id   = cfg.get('voice_id', 0)
        self.timeout    = cfg.get('listen_timeout', 8)
        self.phrase_lim = cfg.get('phrase_time_limit', 12)
        self.cal_dur    = cfg.get('calibration_duration', 0.3)

        # Neural TTS settings (edge-tts)
        self.use_neural     = cfg.get('use_neural_voice', True)
        self.neural_voice   = cfg.get('neural_voice', 'en-IN-NeerjaNeural')
        self.gujarati_voice = cfg.get('gujarati_voice', 'gu-IN-DhwaniNeural')
        self.hindi_voice    = cfg.get('hindi_voice', 'hi-IN-SwaraNeural')
        self._stop_requested = False
        self._is_speaking   = False
        self.current_mood   = "STANDBY"

        # Speech recognition
        self.recognizer   = sr.Recognizer()
        self._microphone  = None
        self._mic_calibrated = False

        # Callback for UI audio level feedback (set by UI if desired)
        self.on_listening: Optional[Callable] = None   # called with True/False

        # TTS — cached COM object fallback
        self._speaker      = None
        self._tts_engine   = 'none'
        self._pyttsx3_eng  = None   # cached to avoid leak
        self._init_speaker()

    def set_mood(self, mood: str):
        """Sets Maya's current emotional mood to dynamically adapt voice pitch and cadence."""
        self.current_mood = str(mood).upper().strip()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _init_speaker(self):
        """Initialise pygame mixer for neural audio and Windows SAPI SpVoice for fallback."""
        if _HAS_EDGE_TTS:
            try:
                if not pygame.mixer.get_init():
                    # 24kHz or 44.1kHz audio buffer for crisp voice playback
                    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
            except Exception as e:
                print(f"⚠️ Pygame mixer init warning: {e}")

        try:
            pythoncom.CoInitialize()
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            sapi_rate = max(-10, min(10, (self.rate - 170) // 20))
            speaker.Rate = sapi_rate
            voices = speaker.GetVoices()
            if voices.Count > self.voice_id:
                speaker.Voice = voices.Item(self.voice_id)
            self._speaker    = speaker
            self._tts_engine = 'sapi'
        except Exception as e:
            print(f"⚠️ SAPI unavailable, switching to pyttsx3: {e}")
            self._speaker    = None
            self._tts_engine = 'pyttsx3'

    def _is_gujarati(self, text: str) -> bool:
        """Detects if text contains Gujarati Unicode script characters."""
        return bool(re.search(r'[\u0A80-\u0AFF]', text))

    def _is_hindi(self, text: str) -> bool:
        """Detects if text contains Hindi / Devanagari Unicode script characters."""
        return bool(re.search(r'[\u0900-\u097F]', text))

    def _speak_neural(self, text: str) -> bool:
        """Synthesize ultra-realistic speech via edge-tts with emotional pitch and rate modulation."""
        if not _HAS_EDGE_TTS:
            return False

        # Clean text for speech: strip URLs, code symbols, and markdown formatting
        clean_text = re.sub(r'https?://\S+|www\.\S+', 'a web link', text)
        clean_text = re.sub(r'[*_`#~<>{}[\]\\]', ' ', clean_text)
        clean_text = ' '.join(clean_text.split())
        if not clean_text:
            return False

        # Automatically select voice based on language
        if self._is_gujarati(clean_text):
            selected_voice = self.gujarati_voice
        elif self._is_hindi(clean_text):
            selected_voice = self.hindi_voice
        else:
            selected_voice = self.neural_voice
        temp_file = os.path.join(tempfile.gettempdir(), f"maya_voice_{int(time.time() * 1000)}.mp3")

        # Dynamic Emotional Voice Modulation
        rate_mod = 0
        pitch_mod = 0
        mood = getattr(self, 'current_mood', 'STANDBY')
        if mood in ("CHEERFUL", "HAPPY", "EXCITED"):
            rate_mod = +6
            pitch_mod = +3
        elif mood in ("EMPATHETIC", "CARING", "WARM"):
            rate_mod = -4
            pitch_mod = -1
        elif mood in ("PLAYFUL", "WITTY"):
            rate_mod = +4
            pitch_mod = +2
        elif mood in ("ALERT", "URGENT", "CONCERNED"):
            rate_mod = +8
            pitch_mod = +4
        elif mood in ("FOCUSED", "SERIOUS"):
            rate_mod = +1
            pitch_mod = +0

        # Rate and pitch mapping
        rate_diff = int(((self.rate - 170) / 170) * 100) + rate_mod
        rate_str = f"{rate_diff:+d}%" if rate_diff != 0 else "+0%"
        pitch_str = f"{pitch_mod:+d}Hz" if pitch_mod != 0 else "+0Hz"

        async def _synthesize():
            communicate = edge_tts.Communicate(clean_text, selected_voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(temp_file)

        try:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                loop.run_until_complete(asyncio.wait_for(_synthesize(), timeout=3.5))
            finally:
                loop.close()

            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                return False

            self._stop_requested = False
            self._is_speaking = True

            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy() and not self._stop_requested:
                    time.sleep(0.04)

                if self._stop_requested:
                    pygame.mixer.music.stop()

                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass

            finally:
                self._is_speaking = False

            return True

        except Exception as e:
            print(f"⚠️ Neural TTS warning (falling back to SAPI/pyttsx3): {e}")
            return False
        finally:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

    def _get_microphone(self):
        """Lazy-init the microphone on first use."""
        if self._microphone is None:
            try:
                self._microphone = sr.Microphone()
            except Exception as e:
                print(f"⚠️ Microphone init error: {e}")
                return None
        return self._microphone

    def _calibrate_mic(self, source):
        """Run ambient noise calibration once."""
        if not self._mic_calibrated:
            self.recognizer.adjust_for_ambient_noise(source, duration=self.cal_dur)
            self._mic_calibrated = True

    # ------------------------------------------------------------------
    # Voice selection
    # ------------------------------------------------------------------

    def get_available_voices(self) -> list:
        """Returns a list of available SAPI voice names."""
        if self._tts_engine == 'sapi' and self._speaker:
            try:
                voices = self._speaker.GetVoices()
                return [voices.Item(i).GetDescription() for i in range(voices.Count)]
            except Exception:
                pass
        return []

    def set_voice(self, voice_index: int):
        """Switch to a different SAPI voice by index."""
        if self._tts_engine == 'sapi' and self._speaker:
            try:
                voices = self._speaker.GetVoices()
                if voices.Count > voice_index:
                    self._speaker.Voice = voices.Item(voice_index)
                    self.voice_id = voice_index
            except Exception as e:
                print(f"⚠️ Could not switch voice: {e}")

    def set_rate(self, rate: int):
        """Update speech rate (words-per-minute style)."""
        self.rate = rate
        if self._tts_engine == 'sapi' and self._speaker:
            sapi_rate = max(-10, min(10, (rate - 170) // 20))
            try:
                self._speaker.Rate = sapi_rate
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str):
        """Speaks text using Neural Voice (edge-tts). Falls back seamlessly to SAPI or pyttsx3."""
        if not text or not text.strip():
            return

        # Voice Guard: Keep spoken speech concise (1-2 sentences maximum) so Maya never babbles
        text_to_speak = text.strip()
        if len(text_to_speak) > 280:
            sentences = re.split(r'(?<=[.!?।])\s+', text_to_speak)
            if len(sentences) >= 2:
                text_to_speak = ' '.join(sentences[:2]).strip()
            else:
                text_to_speak = text_to_speak[:250].rsplit(' ', 1)[0] + "."

        # 1. Ultra-realistic Neural Voice (Primary)
        if self.use_neural and _HAS_EDGE_TTS:
            if self._speak_neural(text_to_speak):
                return

        # 2. Windows SAPI5 (Fast Offline Fallback)
        if self._tts_engine == 'sapi' and self._speaker:
            try:
                try: pythoncom.CoInitialize()
                except Exception: pass
                self._speaker.Speak(text_to_speak)
                return
            except Exception as e:
                print(f"⚠️ SAPI speak error, falling back: {e}")
                self._tts_engine = 'pyttsx3'

        # 3. pyttsx3 (Secondary Fallback)
        try:
            import pyttsx3
            if self._pyttsx3_eng is None:
                self._pyttsx3_eng = pyttsx3.init()
                self._pyttsx3_eng.setProperty('rate', self.rate)
            self._pyttsx3_eng.say(text)
            self._pyttsx3_eng.runAndWait()
        except Exception as e:
            print(f"⚠️ pyttsx3 fallback error: {e}")
            self._pyttsx3_eng = None

    def stop_speaking(self):
        """Immediately stops any ongoing speech (Neural, SAPI, or pyttsx3)."""
        self._stop_requested = True
        if _HAS_EDGE_TTS:
            try:
                if pygame.mixer.get_init():
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
            except Exception:
                pass
        if self._tts_engine == 'sapi' and self._speaker:
            try:
                self._speaker.Speak("", 3)  # SVSFPurgeBeforeSpeak = 3
            except Exception:
                pass

    def _capture_audio(self):
        """Records audio from mic and returns an sr.AudioData object, or None."""
        try:
            import sounddevice as sd
            import numpy as np
            import queue
            import time
        except ImportError:
            print("⚠️ Missing sounddevice/numpy for microphone fallback.")
            return None

        print("\n🎙️ Listening... (Speak now)")
        if self.on_listening:
            try: self.on_listening(True)
            except Exception: pass

        try:
            q = queue.Queue()
            def callback(indata, frames, t, status):
                q.put(indata.copy())

            fs = 16000
            with sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback):
                start_time = time.time()
                audio_chunks = []
                is_speaking = False
                silence_start = None

                while True:
                    chunk = q.get()
                    energy = np.abs(chunk).mean()

                    if energy > 30:  # Activity threshold
                        if not is_speaking:
                            is_speaking = True
                        silence_start = None
                    else:
                        if is_speaking:
                            if silence_start is None:
                                silence_start = time.time()
                            elif time.time() - silence_start > 1.5:
                                break  # Stop after 1.5s of silence

                    if is_speaking:
                        audio_chunks.append(chunk)
                        if time.time() - start_time > self.phrase_lim:
                            break
                    elif time.time() - start_time > self.timeout:
                        return None  # Global timeout waiting for speech

            if not audio_chunks:
                return None

            audio_data = np.concatenate(audio_chunks).tobytes()
            return sr.AudioData(audio_data, fs, 2)

        except Exception as e:
            print(f"⚠️ Microphone capture error: {e}")
            return None
        finally:
            if self.on_listening:
                try: self.on_listening(False)
                except Exception: pass

    def listen(self) -> str | None:
        """Listens to the microphone and returns the spoken text (English or Gujarati), or None."""
        audio = self._capture_audio()
        if audio is None:
            return None

        print("🔄 Processing...")
        # --- Multilingual: try English first, then Hindi, then Gujarati ---
        languages = [
            ("en-IN", "English"),
            ("hi-IN", "Hindi"),
            ("gu-IN", "Gujarati"),
        ]
        for lang_code, lang_name in languages:
            try:
                text = self.recognizer.recognize_google(audio, language=lang_code)
                if text and text.strip():
                    if lang_name != "English":
                        print(f"🌐 Language detected: {lang_name}")
                        print(f"🗣️ You said ({lang_name}): {text}")
                    else:
                        print(f"🗣️ You said: {text}")
                    return text
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print(f"⚠️ Recognition error ({lang_name}): {e}")
                continue

        return None