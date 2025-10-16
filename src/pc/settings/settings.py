import os.path
import gettext
import sys


YACC_DEBUG = 0
YACC_OPTIMIZE = 1
LEX_OPTIMIZE = 1
PARSE_DEBUG = 0


SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = getattr(sys, "_MEIPASS", SRC_DIR)  # PyInstaller support

LOCALES_DIR = os.path.join(SRC_DIR, "locales")
TEMPLATE_DIR = os.path.join(SRC_DIR, "templates")

"""
print("SETTINGS:", os.path.abspath(__file__))
print("SRC_DIR:", SRC_DIR)
print("LOCALES_DIR:", LOCALES_DIR)
print("TEMPLATE_DIR:", TEMPLATE_DIR)

input("Waiting...")
"""

if SRC_DIR not in sys.path:  # pragma: no cover
    sys.path.append(SRC_DIR)

# gettext.bindtextdomain('messages', LOCALES_DIR)
# gettext.textdomain('messages')
# gettext.install('messages', LOCALES_DIR)
# TRANSLATION_FILE = gettext.find('messages', localedir=LOCALES_DIR, all=True) #, languages=None, all=False)

LANGUAGE = getattr(sys.modules["__main__"], "LANGUAGE", "en_US")

TRANSLATION = gettext.translation(
    "messages", localedir=LOCALES_DIR, languages=[LANGUAGE]
)
_ = TRANSLATION.gettext
