def clean(original: str) -> str:
    """Clean up the mixed HTML code in the sentence.

    Parameters
    ----------
    original: str
        The sentence.

    Return
    ------
    str
        The clear sentence.
    """
    ...  # TODO


def word_segmentation(text: str) -> list[str]:
    """Divide sentences into words.

    Only importent words will return.

    Parameters
    ----------
    text: str
        The clear sentence.

    Return
    ------
    list[str]
        The list of words.
    """
    ...  # TODO: word segmentation and filter


def emotional_analysis(text: str) -> float:
    """Analyze the emotion of the sentence.

    Parameters
    ----------
    text: str
        The clear sentence.

    Return
    ------
    float
        A score between `-1.0` and `1.0`.
        `-1.0` means extreme negative emotions,
        and `1.0` means extreme positive emotions.
    """
    ...  # TODO


def text_embedding(text: str) -> ...:
    """Embedding the text to a vector.

    Parameters
    ----------
    text: str
        The text.

    Return
    ------
    ...
        The embedding vector.
    """
    ...  # TODO


def analysis_tieba():
    # get all comments
    # word_segmentation
    # emotional_analysis
    # text embedding
    # store the analysis results
    ...  # TODO
