from gtts import gTTS

def phat_am(word):
    tts = gTTS(text=word, lang='en')
    tts.save("speech.mp3")
    return "speech.mp3"