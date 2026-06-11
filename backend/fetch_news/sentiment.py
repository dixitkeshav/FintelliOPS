"""
FinBERT sentiment — model loads lazily on first use so Django can start without Hugging Face download.
"""
import logging
import threading

from torch.nn.functional import softmax
import torch

logger = logging.getLogger(__name__)

_tokenizer = None
_model = None
_load_lock = threading.Lock()
_MODEL_NAME = "yiyanghkust/finbert-tone"


def _get_model():
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return _tokenizer, _model
    with _load_lock:
        if _tokenizer is not None and _model is not None:
            return _tokenizer, _model
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            logger.info("Loading FinBERT model %s (first call may download weights)...", _MODEL_NAME)
            _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
            _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        except Exception as e:
            logger.exception("Failed to load FinBERT: %s", e)
            raise
    return _tokenizer, _model


def analyze_financial_sentiment(text):
    tokenizer, model = _get_model()
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    outputs = model(**inputs)
    probs = softmax(outputs.logits, dim=1)
    labels = ["negative", "neutral", "positive"]
    sentiment = labels[torch.argmax(probs)]
    return sentiment, probs.detach().numpy().tolist()[0]
