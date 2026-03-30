class ColorChart:
    """Pastel visionOS glassmorphism palette — mobile-first."""

    # Backgrounds
    BG_GRADIENT = "linear-gradient(150deg, #cfe0ff 0%, #eef2ff 45%, #e2d9ff 100%)"
    GLASS_BG = "rgba(255, 255, 255, 0.72)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.92)"
    GLASS_SHADOW = "0 8px 32px rgba(110, 120, 200, 0.10), 0 2px 8px rgba(110, 120, 200, 0.06)"

    # Text
    TEXT_MAIN = "#2c2c3a"
    TEXT_MUTED = "#7a7a90"
    TEXT_SUBTLE = "#b0b0c4"

    # Accent — pastel periwinkle/indigo
    ACCENT_PRIMARY = "#7b9cf4"
    ACCENT_SOFT = "rgba(123, 156, 244, 0.15)"
    ACCENT_BORDER = "rgba(123, 156, 244, 0.38)"

    # Semantic — pastel
    SUCCESS_COLOR = "#6ee7b7"   # pastel mint
    WARNING_COLOR = "#fcd34d"   # pastel yellow
    DANGER_COLOR = "#fca5a5"    # pastel rose
    YELLOW = "#fcd34d"

    # Verdict scale — pastel
    VERDICT_COLORS = {
        "true": "#6ee7b7",
        "very likely true": "#86efac",
        "uncertain": "#fcd34d",
        "very likely false": "#fdba74",
        "false": "#fca5a5",
        "error": "#fca5a5",
    }

    @classmethod
    def verdict_color(cls, verdict: str) -> str:
        return cls.VERDICT_COLORS.get(verdict.lower(), cls.TEXT_MUTED)

    @classmethod
    def get_bg_main(cls) -> str:
        return cls.GLASS_BG

    @classmethod
    def get_bg_sidebar(cls) -> str:
        return cls.GLASS_BG

    @classmethod
    def get_bg_card(cls) -> str:
        return cls.GLASS_BG

    @classmethod
    def get_accent_primary(cls) -> str:
        return cls.ACCENT_PRIMARY

    @classmethod
    def get_accent_soft(cls) -> str:
        return cls.ACCENT_SOFT

    @classmethod
    def get_text_main(cls) -> str:
        return cls.TEXT_MAIN

    @classmethod
    def get_text_muted(cls) -> str:
        return cls.TEXT_MUTED

    @classmethod
    def get_success_color(cls) -> str:
        return cls.SUCCESS_COLOR

    @classmethod
    def get_warning_color(cls) -> str:
        return cls.WARNING_COLOR

    @classmethod
    def get_yellow(cls) -> str:
        return cls.YELLOW
