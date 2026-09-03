from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

class IndonesianNLP:
    def __init__(self):
        # Initialize Stemmer
        stemmer_factory = StemmerFactory()
        self.stemmer = stemmer_factory.create_stemmer()
        
        # Initialize Stopword Remover
        stopword_factory = StopWordRemoverFactory()
        self.stopword_remover = stopword_factory.create_stop_word_remover()
        
    def process(self, text):
        """
        Removes stopwords and stems the text.
        Assumes the text is already cleaned (lowercased, alphabetic only).
        """
        if not text:
            return ""
            
        # 1. Stopword Removal
        text = self.stopword_remover.remove(text)
        
        # 2. Stemming
        text = self.stemmer.stem(text)
        
        return text

# Singleton instance to be imported and used
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = IndonesianNLP()
    return _nlp

def process_text(text):
    nlp = get_nlp()
    return nlp.process(text)
