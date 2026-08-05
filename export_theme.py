"""計画表出力（Excel / PDF）のカラーテーマ定義（SSOT）

色は '#' なしの6桁HEX文字列で保持する。
- Excel(openpyxl): そのまま fgColor / Font(color=) に渡せる
- PDF(reportlab): hexc() で colors.HexColor に変換して使う
"""

THEMES = {
    # 現行のダークテーマ（アプリのCSSに準拠）
    "dark": {
        "bg_main":           "0C0D11",
        "bg_surface":        "13151E",
        "bg_surface2":       "1B1E2B",
        "bg_header":         "222536",
        "bg_title":          "0F1119",
        "bg_day_a":          "13151E",
        "bg_day_b":          "1B1E2B",
        "text":              "DDE1EC",
        "muted":             "9AA3B8",
        "dim":               "555D7A",
        "blue":              "5B8FF9",
        "green":             "3ECF8E",
        "amber":             "F5A623",
        "rose":              "F06292",
        "red":               "EF4444",
        "border":            "252838",
        "border_light":      "2F3347",
        "unassigned_bg":     "1A0A0A",
        "unassigned_border": "3A1010",
    },
    # 印刷向けのライトテーマ
    "light": {
        "bg_main":           "FFFFFF",
        "bg_surface":        "FAFBFC",
        "bg_surface2":       "F1F3F7",
        "bg_header":         "E7EAF1",
        "bg_title":          "EEF2FB",
        "bg_day_a":          "FFFFFF",
        "bg_day_b":          "F4F6FA",
        "text":              "1A1D26",
        "muted":             "4A5169",
        "dim":               "8A91A6",
        "blue":              "1D4ED8",
        "green":             "0B7A55",
        "amber":             "A15C07",
        "rose":              "C2185B",
        "red":               "C62828",
        "border":            "D8DDE8",
        "border_light":      "B4BCCD",
        "unassigned_bg":     "FDF0F0",
        "unassigned_border": "E8B4B4",
    },
}

DEFAULT_THEME = "dark"


def normalize_theme(theme=None):
    """テーマ名を正規化する（未知の値はダーク扱い）"""
    t = (theme or DEFAULT_THEME).strip().lower()
    return t if t in THEMES else DEFAULT_THEME


def get_palette(theme=None):
    """テーマ名からカラーパレット（dict）を返す"""
    return dict(THEMES[normalize_theme(theme)])
