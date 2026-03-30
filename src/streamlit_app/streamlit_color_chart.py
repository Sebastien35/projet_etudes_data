class ColorChart:
    """Light-mode visionOS glassmorphism palette."""

    # Backgrounds
    BG_GRADIENT = "linear-gradient(135deg, #e8f0fe 0%, #f5f7ff 50%, #ede8ff 100%)"
    GLASS_BG = "rgba(255, 255, 255, 0.65)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.85)"
    GLASS_SHADOW = "0 8px 32px rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)"

    # Text
    TEXT_MAIN = "#1C1C1E"
    TEXT_MUTED = "#6E6E73"
    TEXT_SUBTLE = "#AEAEB2"

    # Accent (visionOS blue)
    ACCENT_PRIMARY = "#007AFF"
    ACCENT_SOFT = "rgba(0, 122, 255, 0.12)"
    ACCENT_BORDER = "rgba(0, 122, 255, 0.28)"

    # Semantic
    SUCCESS_COLOR = "#34C759"
    WARNING_COLOR = "#FF9F0A"
    DANGER_COLOR = "#FF3B30"
    YELLOW = "#FF9F0A"

    # Verdict scale
    VERDICT_COLORS = {
        "true": "#34C759",
        "very likely true": "#30D158",
        "uncertain": "#FF9F0A",
        "very likely false": "#FF6B35",
        "false": "#FF3B30",
        "error": "#FF3B30",
    }

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

    @classmethod
    def verdict_color(cls, verdict: str) -> str:
        return cls.VERDICT_COLORS.get(verdict.lower(), cls.TEXT_MUTED)
