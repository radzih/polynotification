from pathlib import Path
from fluentogram import TranslatorHub, FluentTranslator
from fluent_compiler.bundle import FluentBundle


class FluentResource:
    """Resource wrapper for fluent-compiler"""
    def __init__(self, text: str, filename: str = "messages.ftl"):
        self.text = text
        self.filename = filename


def setup_i18n() -> TranslatorHub:
    # Load FTL file content
    ftl_path = Path("src/locales/uk/messages.ftl")
    ftl_content = ftl_path.read_text(encoding="utf-8")
    
    # Create resource object
    resource = FluentResource(ftl_content, filename="messages.ftl")
    
    # Create FluentBundle
    bundle = FluentBundle("uk", [resource], use_isolating=False)
    
    return TranslatorHub(
        {"uk": ("uk",)},
        [
            FluentTranslator(
                locale="uk",
                translator=bundle,
            )
        ],
        root_locale="uk",
    )
