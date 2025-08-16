import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


def remove_stopwords(text):
    # Download stopwords if not already present
    try:
        stop_words = set(stopwords.words("english"))
    except LookupError:
        nltk.download("stopwords")
        stop_words = set(stopwords.words("english"))

    words = text.split()
    filtered = [w for w in words if w.lower() not in stop_words]
    return " ".join(filtered)


def lemmatize_text(text):
    # Download wordnet if not already present
    try:
        lemmatizer = WordNetLemmatizer()
        lemmatizer.lemmatize("test")
    except LookupError:
        nltk.download("wordnet")
        lemmatizer = WordNetLemmatizer()

    words = text.split()
    lemmatized = [lemmatizer.lemmatize(w) for w in words]
    return " ".join(lemmatized)
