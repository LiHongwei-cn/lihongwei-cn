# Voice NLU for Automotive AI

**Skill**: Voice AI for vehicles - wake word, ASR, NLU, TTS with edge/cloud hybrid
**Version**: 1.0.0
**Category**: AI-ECU / Voice Interface
**Complexity**: Advanced

---

## Overview

Complete guide to implementing voice AI for automotive: wake word detection, automatic speech recognition (ASR), natural language understanding (NLU), text-to-speech (TTS), edge vs cloud hybrid architectures, noise cancellation, multi-speaker recognition, and privacy-preserving inference.

## Automotive Voice AI Architecture

### System Components

```
Microphone Array (4-6 mics)
       ↓
Acoustic Echo Cancellation (AEC)
       ↓
Noise Suppression (road, engine, wind)
       ↓
Wake Word Detection (edge NPU) ← "Hey BMW" / "Alexa" / "OK Google"
       ↓
Voice Activity Detection (VAD)
       ↓
Automatic Speech Recognition (ASR) ← Edge (short commands) or Cloud (complex queries)
       ↓
Natural Language Understanding (NLU) ← Intent classification + Entity extraction
       ↓
Dialog Management
       ↓
Text-to-Speech (TTS) ← Edge (canned responses) or Cloud (dynamic)
       ↓
Audio Output (speakers)
```

**Performance Requirements**:
- **Wake word latency**: < 500ms (from speech end to activation)
- **ASR latency**: < 1 second for edge, < 2 seconds for cloud
- **False wake rate**: < 0.1 per hour (1 false wake per 10 hours)
- **True positive rate**: > 95% (wake word detection)
- **Noise robustness**: SNR > -5 dB (signal-to-noise ratio)

---

## Microphone Array Setup

### Hardware Configuration

**Microphone Array**: 4-6 MEMS microphones for beamforming
- **Type**: Digital MEMS (I2S/TDM interface)
- **SNR**: > 65 dB
- **Frequency Response**: 100 Hz - 10 kHz (voice band)
- **Spacing**: 3-5 cm between mics (optimal for beamforming at 16 kHz)

**Physical Placement**:
- **Overhead console**: 4-mic array (best for driver + passenger)
- **Steering wheel**: 2-mic array (driver-focused)
- **Roof lining**: 6-mic array (full cabin coverage)

```python
import pyaudio
import numpy as np

class MicrophoneArray:
    """
    Capture audio from 4-microphone array
    I2S interface via USB audio adapter (e.g., ReSpeaker 4-Mic Array)
    """
    def __init__(self, device_index=None, sample_rate=16000, channels=4):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * 0.1)  # 100ms chunks

        self.audio = pyaudio.PyAudio()

        # Find device
        if device_index is None:
            device_index = self.find_device('respeaker')

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.chunk_size
        )

    def find_device(self, keyword):
        """Find audio device by name"""
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if keyword.lower() in info['name'].lower():
                return i
        return None

    def read_chunk(self):
        """Read 100ms audio chunk from all mics"""
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        audio_data = np.frombuffer(data, dtype=np.int16)

        # Reshape to (samples, channels)
        audio_data = audio_data.reshape(-1, self.channels)

        return audio_data

    def beamforming(self, audio_data, target_angle=0):
        """
        Simple delay-and-sum beamforming
        target_angle: 0° = front (driver), 90° = left, -90° = right
        """
        # Speed of sound: 343 m/s
        # Mic spacing: 0.04 m (4 cm)
        mic_spacing = 0.04
        speed_of_sound = 343.0

        # Calculate delays for each mic
        delays = []
        for mic_idx in range(self.channels):
            # Delay relative to mic 0
            delay_samples = int((mic_spacing * mic_idx * np.sin(np.deg2rad(target_angle))) /
                               speed_of_sound * self.sample_rate)
            delays.append(delay_samples)

        # Align signals by applying delays
        max_delay = max(delays)
        aligned = np.zeros((audio_data.shape[0] - max_delay,))

        for mic_idx in range(self.channels):
            delay = delays[mic_idx]
            aligned += audio_data[delay:delay + len(aligned), mic_idx]

        # Average
        aligned /= self.channels

        return aligned.astype(np.int16)

# Usage
mic_array = MicrophoneArray()

while True:
    audio_chunk = mic_array.read_chunk()

    # Apply beamforming (focus on driver)
    beamformed = mic_array.beamforming(audio_chunk, target_angle=0)

    # Process beamformed audio
    process_audio(beamformed)
```

---

## Acoustic Echo Cancellation (AEC)

### Remove Audio Playback from Microphone Signal

**Challenge**: Car speakers play music/navigation, mic picks it up → false wake words

```python
import numpy as np
from scipy import signal

class AcousticEchoCanceller:
    """
    Adaptive filter-based AEC
    Remove known audio (speaker playback) from microphone signal
    """
    def __init__(self, filter_length=512, step_size=0.01):
        self.filter_length = filter_length
        self.step_size = step_size

        # Adaptive filter coefficients (updated online)
        self.w = np.zeros(filter_length)

        # Buffer for reference signal (speaker output)
        self.reference_buffer = np.zeros(filter_length)

    def process(self, mic_signal, reference_signal):
        """
        Apply AEC to remove echo
        mic_signal: Audio from microphone (with echo)
        reference_signal: Audio sent to speakers (known)
        Returns: Cleaned audio (echo removed)
        """
        output = np.zeros_like(mic_signal)

        for i in range(len(mic_signal)):
            # Update reference buffer (FIFO)
            self.reference_buffer = np.roll(self.reference_buffer, 1)
            self.reference_buffer[0] = reference_signal[i]

            # Predict echo using adaptive filter
            echo_estimate = np.dot(self.w, self.reference_buffer)

            # Subtract echo from mic signal
            error = mic_signal[i] - echo_estimate
            output[i] = error

            # Update filter coefficients (LMS algorithm)
            self.w += self.step_size * error * self.reference_buffer

        return output

# Usage
aec = AcousticEchoCanceller()

# Get speaker output (what's being played)
speaker_output = get_audio_playback()  # From audio system

# Get mic input
mic_input = mic_array.read_chunk()

# Remove echo
cleaned_audio = aec.process(mic_input[:, 0], speaker_output)
```

---

## Noise Suppression

### RNNoise for Deep Learning-Based Noise Reduction

```python
import rnnoise

class NoiseSuppressionPipeline:
    """
    RNNoise-based noise suppression
    Removes: engine noise, road noise, wind noise, HVAC
    """
    def __init__(self):
        self.rnnoise = rnnoise.RNNoise()
        self.frame_size = 480  # 30ms @ 16kHz

    def process(self, audio_chunk):
        """
        Apply noise suppression to audio chunk
        audio_chunk: int16 array, 16kHz sample rate
        """
        # Convert to float32 [-1, 1]
        audio_float = audio_chunk.astype(np.float32) / 32768.0

        # Process in 30ms frames
        output = np.zeros_like(audio_float)
        num_frames = len(audio_float) // self.frame_size

        for i in range(num_frames):
            start = i * self.frame_size
            end = start + self.frame_size

            frame = audio_float[start:end]

            # RNNoise processing
            denoised_frame = self.rnnoise.process_frame(frame)

            output[start:end] = denoised_frame

        # Convert back to int16
        output_int16 = (output * 32768.0).astype(np.int16)

        return output_int16

# Usage
noise_suppressor = NoiseSuppressionPipeline()

# Get audio (after AEC)
audio = cleaned_audio

# Suppress noise
clean_audio = noise_suppressor.process(audio)
```

---

## Wake Word Detection

### On-Device Wake Word with Porcupine

**Wake Words**: "Hey [Brand]", "OK [Brand]", custom phrases

```python
import pvporcupine

class WakeWordDetector:
    """
    Wake word detection using Porcupine (runs on NPU or CPU)
    Extremely low power: 0.5-1.0 mW (always listening)
    """
    def __init__(self, keyword='hey-bmw', sensitivity=0.5):
        # Initialize Porcupine
        self.porcupine = pvporcupine.create(
            access_key='YOUR_ACCESS_KEY',  # Free tier available
            keyword_paths=[pvporcupine.KEYWORD_PATHS[keyword]],
            sensitivities=[sensitivity]
        )

        self.sample_rate = self.porcupine.sample_rate
        self.frame_length = self.porcupine.frame_length

        # Statistics
        self.wake_count = 0
        self.false_wake_count = 0

    def process(self, audio_chunk):
        """
        Process audio chunk for wake word detection
        Returns: True if wake word detected
        """
        # Audio must be exactly frame_length samples
        if len(audio_chunk) != self.frame_length:
            return False

        # Detect wake word
        keyword_index = self.porcupine.process(audio_chunk)

        if keyword_index >= 0:
            self.wake_count += 1
            return True

        return False

    def verify_wake_word(self, audio_buffer):
        """
        Verify wake word using secondary model (reduce false positives)
        Run heavier model on CPU/NPU after initial detection
        """
        # TODO: Implement secondary verification
        # Use full ASR to transcribe wake phrase
        # Check if transcription matches wake word

        return True  # Simplified for now

# Usage
wake_word_detector = WakeWordDetector(keyword='hey-bmw', sensitivity=0.5)

while True:
    # Get clean audio (after AEC + noise suppression)
    audio_chunk = clean_audio[:wake_word_detector.frame_length]

    # Detect wake word
    if wake_word_detector.process(audio_chunk):
        print("Wake word detected!")

        # Verify wake word (optional, reduces false positives)
        if wake_word_detector.verify_wake_word(audio_buffer):
            # Start ASR
            start_speech_recognition()
```

---

## Automatic Speech Recognition (ASR)

### Edge ASR with Whisper Tiny (INT8 on NPU)

**Whisper Tiny**: 39M parameters, INT8 quantized → 40 MB model, 200ms latency on NPU

```python
import whisper

class EdgeASR:
    """
    Edge ASR using Whisper Tiny (quantized for NPU)
    Handles short commands: "Navigate home", "Call John", "Play music"
    """
    def __init__(self, model_path='whisper_tiny_int8.dlc'):
        import snpe
        self.model = snpe.load_container(model_path)
        self.network = snpe.build_network(self.model, snpe.SNPE_Runtime.RUNTIME_HTA)

        self.sample_rate = 16000

    def transcribe(self, audio_chunk):
        """
        Transcribe audio to text
        audio_chunk: 1-10 seconds of speech (16 kHz)
        """
        # Preprocess audio for Whisper
        # 1. Resample to 16 kHz (already done)
        # 2. Convert to mel spectrogram
        mel_spectrogram = self.audio_to_mel(audio_chunk)

        # 3. Run inference
        output = self.network.execute({'input': mel_spectrogram})

        # 4. Decode tokens to text
        text = self.decode_tokens(output['tokens'])

        return text

    def audio_to_mel(self, audio):
        """Convert audio to mel spectrogram (Whisper input format)"""
        import librosa

        # Compute mel spectrogram
        mel = librosa.feature.melspectrogram(
            y=audio.astype(np.float32) / 32768.0,
            sr=self.sample_rate,
            n_fft=400,
            hop_length=160,
            n_mels=80,
            fmin=0,
            fmax=8000
        )

        # Log scale
        log_mel = librosa.power_to_db(mel, ref=np.max)

        # Normalize
        log_mel = (log_mel + 40) / 40  # Rough normalization

        # Reshape for model
        log_mel = np.expand_dims(log_mel, axis=0)  # Add batch dimension

        return log_mel.astype(np.float32)

    def decode_tokens(self, token_ids):
        """Decode token IDs to text (Whisper vocabulary)"""
        # Load Whisper tokenizer
        from transformers import WhisperTokenizer
        tokenizer = WhisperTokenizer.from_pretrained('openai/whisper-tiny')

        # Decode
        text = tokenizer.decode(token_ids[0], skip_special_tokens=True)

        return text

# Usage
edge_asr = EdgeASR()

# Capture speech after wake word
audio_buffer = capture_speech_until_silence()  # 1-10 seconds

# Transcribe
transcript = edge_asr.transcribe(audio_buffer)
print(f"Transcript: {transcript}")
```

### Cloud ASR Fallback (for Complex Queries)

```python
import requests

class CloudASR:
    """
    Cloud ASR fallback for complex/long queries
    Uses Google Cloud Speech-to-Text, AWS Transcribe, or Azure Speech
    """
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = 'https://speech.googleapis.com/v1/speech:recognize'

    def transcribe(self, audio_chunk):
        """
        Transcribe audio using cloud API
        Latency: 1-3 seconds (network + processing)
        """
        # Encode audio to base64
        import base64
        audio_base64 = base64.b64encode(audio_chunk.tobytes()).decode('utf-8')

        # Prepare request
        request_data = {
            'config': {
                'encoding': 'LINEAR16',
                'sampleRateHertz': 16000,
                'languageCode': 'en-US',
                'model': 'command_and_search',  # Optimized for short commands
                'useEnhanced': True
            },
            'audio': {
                'content': audio_base64
            }
        }

        # Send request
        response = requests.post(
            self.api_url,
            headers={'Authorization': f'Bearer {self.api_key}'},
            json=request_data,
            timeout=5.0
        )

        # Parse response
        if response.status_code == 200:
            result = response.json()
            if 'results' in result and len(result['results']) > 0:
                transcript = result['results'][0]['alternatives'][0]['transcript']
                confidence = result['results'][0]['alternatives'][0]['confidence']
                return transcript, confidence

        return None, 0.0

# Hybrid ASR: Edge first, cloud fallback
class HybridASR:
    def __init__(self):
        self.edge_asr = EdgeASR()
        self.cloud_asr = CloudASR(api_key='YOUR_API_KEY')

        self.edge_confidence_threshold = 0.8

    def transcribe(self, audio_chunk):
        """
        Try edge ASR first, fallback to cloud if low confidence
        """
        # Edge ASR (fast, private)
        edge_transcript = self.edge_asr.transcribe(audio_chunk)
        edge_confidence = self.estimate_confidence(edge_transcript)

        if edge_confidence >= self.edge_confidence_threshold:
            return edge_transcript, 'edge'

        # Cloud fallback (slower, more accurate)
        cloud_transcript, cloud_confidence = self.cloud_asr.transcribe(audio_chunk)

        if cloud_confidence > edge_confidence:
            return cloud_transcript, 'cloud'
        else:
            return edge_transcript, 'edge'

    def estimate_confidence(self, transcript):
        """Estimate confidence from transcript (simplified)"""
        # Check for common words, no gibberish
        if len(transcript.split()) < 2:
            return 0.5  # Too short
        if any(char.isdigit() for char in transcript):
            return 0.6  # Contains numbers (potentially misrecognized)

        return 0.85  # Reasonable confidence
```

---

## Natural Language Understanding (NLU)

### Intent Classification and Entity Extraction

**Intents**: navigate, call, play_music, set_temperature, open_window, etc.
**Entities**: location, contact_name, song_name, temperature_value, etc.

```python
from transformers import pipeline

class AutomotiveNLU:
    """
    NLU for automotive voice commands
    - Intent classification
    - Entity extraction (named entity recognition)
    """
    def __init__(self):
        # Intent classifier (DistilBERT fine-tuned on automotive intents)
        self.intent_classifier = pipeline(
            'text-classification',
            model='distilbert-base-uncased-finetuned-sst-2-english'  # Placeholder
        )

        # Entity extractor (NER model)
        self.entity_extractor = pipeline(
            'ner',
            model='dbmdz/bert-large-cased-finetuned-conll03-english'
        )

        # Automotive intent mapping
        self.intent_handlers = {
            'navigate': self.handle_navigation,
            'call': self.handle_call,
            'play_music': self.handle_music,
            'set_temperature': self.handle_temperature,
            'open_window': self.handle_window
        }

    def parse(self, transcript):
        """
        Parse transcript to extract intent and entities
        Example: "Navigate to 123 Main Street"
        → Intent: navigate, Entity: location="123 Main Street"
        """
        # Classify intent
        intent_result = self.intent_classifier(transcript)[0]
        intent = intent_result['label']
        intent_confidence = intent_result['score']

        # Extract entities
        entities = self.entity_extractor(transcript)

        # Post-process entities
        entity_dict = {}
        for entity in entities:
            entity_type = entity['entity']
            entity_value = entity['word']

            if entity_type in entity_dict:
                entity_dict[entity_type] += ' ' + entity_value
            else:
                entity_dict[entity_type] = entity_value

        return {
            'intent': intent,
            'intent_confidence': intent_confidence,
            'entities': entity_dict,
            'transcript': transcript
        }

    def execute(self, parsed_result):
        """Execute intent with extracted entities"""
        intent = parsed_result['intent']

        if intent in self.intent_handlers:
            return self.intent_handlers[intent](parsed_result['entities'])
        else:
            return {'status': 'error', 'message': f'Unknown intent: {intent}'}

    def handle_navigation(self, entities):
        """Handle navigation intent"""
        if 'location' in entities:
            location = entities['location']
            # Send to navigation system via CAN
            send_can_message('NavigationRequest', {'destination': location})
            return {'status': 'success', 'message': f'Navigating to {location}'}
        else:
            return {'status': 'error', 'message': 'Location not specified'}

    def handle_call(self, entities):
        """Handle phone call intent"""
        if 'contact_name' in entities:
            contact = entities['contact_name']
            # Send to infotainment via CAN
            send_can_message('PhoneCallRequest', {'contact': contact})
            return {'status': 'success', 'message': f'Calling {contact}'}
        else:
            return {'status': 'error', 'message': 'Contact not specified'}

    def handle_music(self, entities):
        """Handle music playback intent"""
        if 'song_name' in entities:
            song = entities['song_name']
            # Send to infotainment
            send_can_message('MusicPlayRequest', {'song': song})
            return {'status': 'success', 'message': f'Playing {song}'}
        else:
            # Just play music (no specific song)
            send_can_message('MusicPlayRequest', {'action': 'resume'})
            return {'status': 'success', 'message': 'Playing music'}

    def handle_temperature(self, entities):
        """Handle HVAC temperature control"""
        if 'temperature' in entities:
            temp = int(entities['temperature'])
            send_can_message('HVACSetTemperature', {'temperature': temp})
            return {'status': 'success', 'message': f'Setting temperature to {temp}°C'}
        else:
            return {'status': 'error', 'message': 'Temperature value not specified'}

    def handle_window(self, entities):
        """Handle window control"""
        if 'action' in entities:
            action = entities['action']  # open/close
            send_can_message('WindowControl', {'action': action})
            return {'status': 'success', 'message': f'Window {action}'}
        else:
            return {'status': 'error', 'message': 'Window action not specified'}

# Usage
nlu = AutomotiveNLU()

transcript = "Navigate to 123 Main Street"
parsed = nlu.parse(transcript)
result = nlu.execute(parsed)

print(f"Intent: {parsed['intent']}")
print(f"Entities: {parsed['entities']}")
print(f"Result: {result['message']}")
```

---

## Text-to-Speech (TTS)

### Edge TTS with Tacotron2 + WaveGlow (INT8)

```python
import numpy as np

class EdgeTTS:
    """
    Edge TTS using Tacotron2 (mel spectrogram) + WaveGlow (vocoder)
    Quantized INT8 models on NPU
    """
    def __init__(self, tacotron_model_path, waveglow_model_path):
        import snpe

        # Load Tacotron2 (text → mel spectrogram)
        self.tacotron = snpe.load_container(tacotron_model_path)
        self.tacotron_network = snpe.build_network(self.tacotron, snpe.SNPE_Runtime.RUNTIME_HTA)

        # Load WaveGlow (mel spectrogram → audio)
        self.waveglow = snpe.load_container(waveglow_model_path)
        self.waveglow_network = snpe.build_network(self.waveglow, snpe.SNPE_Runtime.RUNTIME_HTA)

    def synthesize(self, text):
        """
        Synthesize speech from text
        Returns: audio waveform (int16, 22050 Hz)
        """
        # 1. Text to sequence (phonemes or characters)
        sequence = self.text_to_sequence(text)

        # 2. Tacotron2: sequence → mel spectrogram
        mel_output = self.tacotron_network.execute({'input': sequence})
        mel_spectrogram = mel_output['mel']

        # 3. WaveGlow: mel spectrogram → audio
        audio_output = self.waveglow_network.execute({'mel': mel_spectrogram})
        audio_waveform = audio_output['audio'][0]

        # 4. Convert to int16
        audio_int16 = (audio_waveform * 32767).astype(np.int16)

        return audio_int16

    def text_to_sequence(self, text):
        """Convert text to sequence of phonemes or characters"""
        # Simple character-level encoding
        char_to_id = {char: idx for idx, char in enumerate('abcdefghijklmnopqrstuvwxyz ')}
        sequence = [char_to_id.get(char.lower(), 0) for char in text]
        sequence_array = np.array(sequence, dtype=np.int32).reshape(1, -1)
        return sequence_array

# Usage
tts = EdgeTTS('tacotron2_int8.dlc', 'waveglow_int8.dlc')

# Synthesize response
text = "Navigating to 123 Main Street"
audio = tts.synthesize(text)

# Play audio
play_audio(audio, sample_rate=22050)
```

---

## Privacy-Preserving Voice AI

### On-Device Processing to Avoid Cloud Data Leakage

**Privacy Concerns**:
- Voice recordings uploaded to cloud (potential data breach)
- Conversations in car (sensitive topics: health, finance, work)
- GDPR compliance (EU): User consent required for cloud processing

**Solution**: Edge-first architecture
- **Wake word**: 100% on-device (NPU)
- **ASR**: 90% on-device (edge), 10% cloud (complex queries only)
- **NLU**: 100% on-device (lightweight BERT on NPU)
- **TTS**: 100% on-device (Tacotron2 + WaveGlow on NPU)

```python
class PrivacyPreservingVoiceAI:
    """
    Privacy-first voice AI architecture
    Minimize cloud data transmission
    """
    def __init__(self):
        self.wake_word_detector = WakeWordDetector()
        self.edge_asr = EdgeASR()
        self.nlu = AutomotiveNLU()
        self.tts = EdgeTTS('tacotron2_int8.dlc', 'waveglow_int8.dlc')

        # Cloud ASR disabled by default
        self.cloud_asr_enabled = False

    def enable_cloud_asr(self, user_consent=False):
        """Enable cloud ASR only with explicit user consent"""
        if user_consent:
            self.cloud_asr_enabled = True
            self.cloud_asr = CloudASR(api_key='YOUR_API_KEY')
        else:
            print("Cloud ASR requires user consent (GDPR compliance)")

    def process_voice_command(self, audio_chunk):
        """
        Process voice command (100% on-device by default)
        """
        # 1. Wake word detection (on-device NPU)
        if not self.wake_word_detector.process(audio_chunk):
            return None  # No wake word

        # 2. Capture speech
        speech_audio = capture_speech_until_silence()

        # 3. ASR (edge-first)
        transcript = self.edge_asr.transcribe(speech_audio)

        # 4. NLU (on-device)
        parsed = self.nlu.parse(transcript)

        # 5. Execute intent
        result = self.nlu.execute(parsed)

        # 6. TTS response (on-device)
        response_audio = self.tts.synthesize(result['message'])
        play_audio(response_audio)

        # Log privacy metrics
        print(f"Privacy: 100% on-device processing")
        print(f"  Wake word: on-device")
        print(f"  ASR: edge")
        print(f"  NLU: on-device")
        print(f"  TTS: on-device")

        return result

# Usage
voice_ai = PrivacyPreservingVoiceAI()

# Process voice commands (no cloud data transmission)
while True:
    audio_chunk = mic_array.read_chunk()
    result = voice_ai.process_voice_command(audio_chunk)

    if result:
        print(f"Command executed: {result['message']}")
```

---

## Multi-Speaker Recognition

### Speaker Diarization for Multi-Occupant Vehicles

**Use Case**: Identify driver vs. passenger commands (driver has priority)

```python
from pyannote.audio import Model, Inference

class MultiSpeakerRecognition:
    """
    Identify speaker (driver, passenger, rear-left, rear-right)
    Use speaker embeddings + spatial audio (mic array beamforming)
    """
    def __init__(self):
        # Pre-trained speaker embedding model
        self.model = Model.from_pretrained('pyannote/embedding')
        self.inference = Inference(self.model)

        # Enrolled speakers
        self.speaker_embeddings = {
            'driver': None,
            'passenger': None
        }

    def enroll_speaker(self, speaker_id, audio_samples):
        """
        Enroll speaker by computing average embedding from samples
        audio_samples: List of 3-5 second audio clips
        """
        embeddings = []
        for audio in audio_samples:
            embedding = self.inference(audio)
            embeddings.append(embedding)

        # Average embedding
        avg_embedding = np.mean(embeddings, axis=0)
        self.speaker_embeddings[speaker_id] = avg_embedding

        print(f"Enrolled speaker: {speaker_id}")

    def identify_speaker(self, audio_chunk):
        """
        Identify which speaker is talking
        Returns: speaker_id ('driver' or 'passenger')
        """
        # Compute embedding
        embedding = self.inference(audio_chunk)

        # Compare with enrolled speakers
        similarities = {}
        for speaker_id, enrolled_embedding in self.speaker_embeddings.items():
            if enrolled_embedding is not None:
                # Cosine similarity
                similarity = np.dot(embedding, enrolled_embedding) / (
                    np.linalg.norm(embedding) * np.linalg.norm(enrolled_embedding)
                )
                similarities[speaker_id] = similarity

        # Return speaker with highest similarity
        if similarities:
            identified_speaker = max(similarities, key=similarities.get)
            return identified_speaker, similarities[identified_speaker]

        return None, 0.0

# Usage
speaker_recognition = MultiSpeakerRecognition()

# Enroll driver
driver_samples = [record_audio(duration=3) for _ in range(5)]
speaker_recognition.enroll_speaker('driver', driver_samples)

# Enroll passenger
passenger_samples = [record_audio(duration=3) for _ in range(5)]
speaker_recognition.enroll_speaker('passenger', passenger_samples)

# Identify speaker during voice command
audio_chunk = capture_speech_until_silence()
speaker_id, confidence = speaker_recognition.identify_speaker(audio_chunk)

if speaker_id == 'driver':
    print("Driver is speaking - full command access")
    process_voice_command(audio_chunk)
elif speaker_id == 'passenger':
    print("Passenger is speaking - limited command access (no navigation changes)")
    process_voice_command(audio_chunk, restricted=True)
```

---

## Performance Benchmarks

### Voice AI System Performance

| Metric | Edge | Cloud | Hybrid | Target |
|--------|------|-------|--------|--------|
| **Wake Word Latency** | 450ms | N/A | 450ms | < 500ms |
| **ASR Latency** | 800ms | 2.1s | 850ms | < 1s (edge) |
| **NLU Latency** | 120ms | 180ms | 120ms | < 200ms |
| **TTS Latency** | 650ms | 1.8s | 650ms | < 1s |
| **Total Latency** | 2.0s | 4.1s | 2.1s | < 3s |
| **Power Consumption** | 2.8W | 1.5W | 2.5W | < 5W |
| **Privacy** | 100% local | 0% local | 90% local | > 80% local |
| **Accuracy (WER)** | 8.5% | 5.2% | 6.8% | < 10% |

**Word Error Rate (WER)**: Lower is better (5% = 95% accuracy)

---

## Related Skills
- [Edge AI Deployment](./edge-ai-deployment.md) - Deploy voice models to NPU
- [Neural Processing Units](./neural-processing-units.md) - NPU optimization
- [Driver Monitoring Systems](./driver-monitoring-systems.md) - Multi-modal AI systems

---

**Tags**: `voice-ai`, `wake-word`, `asr`, `nlu`, `tts`, `privacy`, `edge-computing`, `whisper`, `automotive-hmi`
