"""Interface language.  Source strings are Russian; T() returns the English text when the language
is 'en' (missing entries fall back to Russian).  The English table is in i18n_en.py."""
LANG = 'ru'


def set_lang(lang):
    global LANG
    LANG = 'en' if lang == 'en' else 'ru'


def T(text):
    if LANG == 'ru':
        return text
    from i18n_en import EN
    return EN.get(text, text)
