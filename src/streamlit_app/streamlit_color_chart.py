class ColorChart:
    """Dark glassmorphism — Vision OS inspired, premium dark."""

    # Core background
    BG_BASE = "#050510"
    BG_GRADIENT = "linear-gradient(135deg, #050510 0%, #0d0d2b 50%, #050510 100%)"

    # Glass — ultra-dark frosted
    GLASS_BG = "rgba(255, 255, 255, 0.04)"
    GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
    GLASS_SHADOW = (
        "0 8px 32px rgba(0,0,0,0.55), "
        "0 2px 8px rgba(0,0,0,0.35), "
        "inset 0 1px 0 rgba(255,255,255,0.06)"
    )

    # Text
    TEXT_MAIN = "#e8e8f8"
    TEXT_MUTED = "#7878a0"
    TEXT_SUBTLE = "#44445a"

    # Accent — electric violet
    ACCENT_PRIMARY = "#a78bfa"
    ACCENT_SOFT = "rgba(167, 139, 250, 0.10)"
    ACCENT_BORDER = "rgba(167, 139, 250, 0.22)"
    ACCENT_GLOW = "0 0 24px rgba(167,139,250,0.30)"

    # Semantic
    SUCCESS_COLOR = "#34d399"
    WARNING_COLOR = "#fbbf24"
    DANGER_COLOR = "#f87171"
    YELLOW = "#fbbf24"

    # Verdict scale
    VERDICT_COLORS = {
        "true": "#34d399",
        "very likely true": "#6ee7b7",
        "uncertain": "#fbbf24",
        "very likely false": "#fb923c",
        "false": "#f87171",
        "error": "#f87171",
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
