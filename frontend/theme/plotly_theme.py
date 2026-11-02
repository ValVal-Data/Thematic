import plotly.io as pio

from theme.colors import BG, BLUE, BORDER, LIGHT_BLUE, NAVY, PRIMARY


def register_plotly_theme():
    pio.templates["corporate"] = {
        "layout": {
            "font": {"family": "Segoe UI", "size": 14, "color": NAVY},
            "title": {"font": {"family": "Cambria", "size": 24, "color": NAVY}},
            "paper_bgcolor": BG,
            "plot_bgcolor": BG,
            "hovermode": "x unified",
            "colorway": [PRIMARY, BLUE, LIGHT_BLUE],
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            "xaxis": {"gridcolor": BORDER, "zerolinecolor": BORDER, "showline": False},
            "yaxis": {"gridcolor": BORDER, "zerolinecolor": BORDER, "showline": False},
        }
    }
