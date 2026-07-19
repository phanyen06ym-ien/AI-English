from gtts import gTTS
import pygame

def phat_am(word):
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    tts = gTTS(text=word, lang='en')
    tts.save("speech.mp3")
    return "speech.mp3"


def speak(word):
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    audio_path = phat_am(word)
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    return audio_path
