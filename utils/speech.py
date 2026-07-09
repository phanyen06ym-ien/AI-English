from gtts import gTTS
import os

def phat_am(word):
    tts = gTTS(text=word, lang='en')
    tts.save("speech.mp3")
    return "speech.mp3"


def speak(word):
    """Tạo file phát âm và mở bằng trình phát mặc định của Windows."""
    audio_path = phat_am(word)
    os.startfile(audio_path)
    return audio_path
