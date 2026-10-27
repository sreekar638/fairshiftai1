import React, { useState } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Sparkles } from 'lucide-react';

interface VoiceAssistantProps {
  language: 'en' | 'ta';
  onTranscript?: (text: string) => void;
  readText?: string;
}

export const VoiceAssistant: React.FC<VoiceAssistantProps> = ({ language, onTranscript, readText }) => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);

  const startListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceNotice(language === 'ta' ? 'உலாவி குரல் உள்ளீட்டை ஆதரிக்கவில்லை' : 'Browser does not support Speech Recognition. Please use text input.');
      setTimeout(() => setVoiceNotice(null), 4000);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = language === 'ta' ? 'ta-IN' : 'en-US';
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        setIsListening(true);
        setVoiceNotice(language === 'ta' ? 'கேட்கிறது... தயவுசெய்து பேசுங்கள்' : 'Listening... Speak now');
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        if (onTranscript) {
          onTranscript(transcript);
        }
        setVoiceNotice(`${language === 'ta' ? 'பதிவு செய்யப்பட்டது:' : 'Captured:'} "${transcript}"`);
        setTimeout(() => setVoiceNotice(null), 4000);
      };

      recognition.onerror = (e: any) => {
        console.warn('Speech recognition error:', e);
        setIsListening(false);
        setVoiceNotice(language === 'ta' ? 'குரல் உள்ளீடு பிழை' : 'Mic input unavailable or blocked.');
        setTimeout(() => setVoiceNotice(null), 4000);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err) {
      console.warn(err);
      setIsListening(false);
    }
  };

  const speak = () => {
    if (!('speechSynthesis' in window)) {
      setVoiceNotice('Text-to-speech is not supported in this browser.');
      setTimeout(() => setVoiceNotice(null), 4000);
      return;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const text = readText || (language === 'ta' 
      ? 'பேர்ஷிப்ட் AI-க்கு நல்வரவு. உங்கள் ஷிப்ட் மற்றும் பாதுகாப்பு விவரங்களை இங்கு பார்க்கலாம்.'
      : 'Welcome to FairShift AI. Empowering workers with transparency, clear wages, and proactive safety.');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === 'ta' ? 'ta-IN' : 'en-US';
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="flex items-center gap-2">
      {voiceNotice && (
        <span className="text-xs bg-navy text-white px-2 py-1 rounded shadow-sm animate-pulse">
          {voiceNotice}
        </span>
      )}
      <button
        onClick={speak}
        title={isSpeaking ? "Stop Speech" : "Read Page Aloud (TTS)"}
        className={`p-2 rounded-lg border transition-colors ${
          isSpeaking 
            ? 'bg-teal text-white border-teal' 
            : 'bg-white text-navy hover:bg-slate-100 border-slate-200'
        }`}
      >
        {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
      </button>

      <button
        onClick={startListening}
        title={isListening ? "Listening..." : "Voice Input (Speech Recognition)"}
        className={`p-2 rounded-lg border transition-colors ${
          isListening 
            ? 'bg-critical text-white border-critical animate-pulse' 
            : 'bg-white text-navy hover:bg-slate-100 border-slate-200'
        }`}
      >
        {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
      </button>
    </div>
  );
};
