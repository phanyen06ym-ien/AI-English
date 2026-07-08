from utils.translator import dich_tu
from utils.speech import phat_am

def xu_ly_all(word):
    meaning = dich_tu(word)
    audio_path = phat_am(word)
    return meaning, audio_path