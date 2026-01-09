class ColorChart:
    """Color chart with getters for application theme colors."""
    
    BG_MAIN        = "#0F0F12"
    BG_SIDEBAR     = "#090101"
    BG_CARD        = "#1E1E24"
    ACCENT_PRIMARY = "#E34545"
    ACCENT_SOFT    = "#F87171"
    TEXT_MAIN      = "#EDEDED"
    TEXT_MUTED     = "#9CA3AF"
    SUCCESS_COLOR  = "#22C55E"
    WARNING_COLOR  = "#E34545"
    
    @classmethod
    def get_bg_main(cls) -> str:
        return cls.BG_MAIN
    
    @classmethod
    def get_bg_sidebar(cls) -> str:
        return cls.BG_SIDEBAR
    
    @classmethod
    def get_bg_card(cls) -> str:
        return cls.BG_CARD
    
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