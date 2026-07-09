from googletrans import Translator

def dich_tu(word):
    try:
        translator = Translator()
        return translator.translate(word, dest='vi').text
    except:
        return "Không dịch được"