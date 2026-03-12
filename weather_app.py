"""
╔══════════════════════════════════════════════════════╗
║          SKYE — Desktop Weather Application          ║
║         Built with Python + Tkinter + WeatherAPI     ║
╚══════════════════════════════════════════════════════╝


"""

import tkinter as tk
import requests
import threading
from datetime import datetime

# ══════════════════════════════════════════
#  CONFIG — paste your API key here
# ══════════════════════════════════════════
API_KEY = "e761a81f3679434db1e45232261203"
BASE_URL = "http://api.weatherapi.com/v1"

# ══════════════════════════════════════════
#  COLOUR PALETTE
# ══════════════════════════════════════════
T = {
    "bg_deep":    "#07090f",
    "bg_main":    "#0e1219",
    "bg_card":    "#141925",
    "bg_card2":   "#1a2130",
    "bg_input":   "#1e2736",
    "bg_hover":   "#232f42",
    "blue":       "#4f9cf9",
    "blue_light": "#7bb8ff",
    "blue_dim":   "#2d5fa6",
    "cyan":       "#38e5c5",
    "gold":       "#f9c74f",
    "rose":       "#f97b7b",
    "green":      "#50fa7b",
    "text_bright":"#f0f4ff",
    "text_main":  "#c8d6f0",
    "text_muted": "#6b7fa3",
    "text_dim":   "#3d4f6e",
    "border":     "#1f2d45",
    "border2":    "#2a3d5c",
}

# ══════════════════════════════════════════
#  WEATHER VISUAL MAP
# ══════════════════════════════════════════
VISUALS = {
    "sunny":         ("☀",  "#f9c74f"),
    "clear":         ("☽",  "#4f9cf9"),
    "partly cloudy": ("⛅",  "#7bb8ff"),
    "cloudy":        ("☁",  "#8a9ec4"),
    "overcast":      ("☁",  "#6b7fa3"),
    "mist":          ("≋",  "#8ac4d0"),
    "fog":           ("≋",  "#8ac4d0"),
    "drizzle":       ("⛆",  "#4f9cf9"),
    "rain":          ("⛆",  "#4f9cf9"),
    "snow":          ("❄",  "#c8e6ff"),
    "sleet":         ("⛆",  "#a0c4e8"),
    "thunder":       ("⚡",  "#f9c74f"),
    "blizzard":      ("❄",  "#c8e6ff"),
    "hail":          ("⛆",  "#8ac4d0"),
}

def get_visual(condition_text):
    text = condition_text.lower()
    for key, val in VISUALS.items():
        if key in text:
            return val
    return ("◈", T["blue"])

# ══════════════════════════════════════════
#  API + PARSING
# ══════════════════════════════════════════
def fetch_forecast(city, days=7):
    url = f"{BASE_URL}/forecast.json"
    r = requests.get(url, params={
        "key": API_KEY, "q": city, "days": days, "aqi": "yes"
    }, timeout=10)
    r.raise_for_status()
    return r.json()

def parse_data(raw):
    loc = raw["location"]
    cur = raw["current"]
    aqi_val = cur.get("air_quality", {}).get("us-epa-index", 0)
    aqi_map = {1:"Good", 2:"Moderate", 3:"Unhealthy*", 4:"Unhealthy", 5:"Very Unhealthy", 6:"Hazardous"}

    weather = {
        "city":     loc["name"],
        "country":  loc["country"],
        "localtime":loc["localtime"],
        "temp_c":   cur["temp_c"],    "temp_f":  cur["temp_f"],
        "feels_c":  cur["feelslike_c"],"feels_f": cur["feelslike_f"],
        "condition":cur["condition"]["text"],
        "humidity": cur["humidity"],
        "wind_kph": cur["wind_kph"],  "wind_dir":cur["wind_dir"],
        "uv":       cur["uv"],
        "vis_km":   cur["vis_km"],
        "pressure": cur["pressure_mb"],
        "aqi":      aqi_map.get(int(aqi_val), "—") if aqi_val else "—",
    }

    forecast = []
    for d in raw["forecast"]["forecastday"]:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        forecast.append({
            "day":     dt.strftime("%A"),
            "date":    dt.strftime("%b %d"),
            "max_c":   d["day"]["maxtemp_c"],  "min_c": d["day"]["mintemp_c"],
            "max_f":   d["day"]["maxtemp_f"],  "min_f": d["day"]["mintemp_f"],
            "condition":d["day"]["condition"]["text"],
            "rain_pct":d["day"]["daily_chance_of_rain"],
        })

    hourly = []
    now_h = datetime.now().hour
    for h in raw["forecast"]["forecastday"][0]["hour"]:
        hr = datetime.strptime(h["time"], "%Y-%m-%d %H:%M").hour
        if hr >= now_h:
            hourly.append({
                "hour":  datetime.strptime(h["time"], "%Y-%m-%d %H:%M").strftime("%I %p").lstrip("0"),
                "temp_c":h["temp_c"], "temp_f":h["temp_f"],
                "cond":  h["condition"]["text"],
            })
            if len(hourly) == 8:
                break

    return weather, forecast, hourly


# ══════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════
class SkyeWeather:

    def __init__(self, root):
        self.root = root
        self.celsius = True
        self._w = self._fc = self._hr = None
        self._setup_window()
        self._build()
        self.root.after(500, lambda: self._do_search("Mumbai"))

    # ── WINDOW ─────────────────────────────
    def _setup_window(self):
        self.root.title("SKYE Weather")
        self.root.configure(bg=T["bg_main"])
        self.root.state("zoomed")
        self.root.resizable(True, True)
        # Fallback for non-Windows
        try:
            self.root.state("zoomed")
        except Exception:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh}+0+0")

    # ── BUILD ──────────────────────────────
    def _build(self):
        # ── Sidebar (left 27%)
        self.sidebar = tk.Frame(self.root, bg=T["bg_card"], bd=0)
        self.sidebar.place(relx=0, rely=0, relwidth=0.27, relheight=1)
        self._build_sidebar()

        # ── Content (right 73%)
        self.content = tk.Frame(self.root, bg=T["bg_main"], bd=0)
        self.content.place(relx=0.27, rely=0, relwidth=0.73, relheight=1)
        self._build_content()

    # ── SIDEBAR ────────────────────────────
    def _build_sidebar(self):
        s = self.sidebar

        # App name
        tk.Label(s, text="SKYE", bg=T["bg_card"], fg=T["blue"],
                 font=("Segoe UI", 26, "bold"), anchor="w"
                 ).place(relx=0.08, rely=0.022)
        tk.Label(s, text="WEATHER DASHBOARD", bg=T["bg_card"], fg=T["text_dim"],
                 font=("Segoe UI", 7, "bold"), anchor="w"
                 ).place(relx=0.08, rely=0.062)

        tk.Frame(s, bg=T["border"], height=1
                 ).place(relx=0.06, rely=0.098, relwidth=0.88)

        # Search label
        tk.Label(s, text="SEARCH CITY", bg=T["bg_card"], fg=T["text_dim"],
                 font=("Segoe UI", 8, "bold"), anchor="w"
                 ).place(relx=0.08, rely=0.112)

        # Entry + button
        ef = tk.Frame(s, bg=T["bg_input"])
        ef.place(relx=0.06, rely=0.133, relwidth=0.88, height=44)

        self.entry = tk.Entry(ef, bg=T["bg_input"], fg=T["text_bright"],
                              insertbackground=T["blue"], relief="flat",
                              font=("Segoe UI", 12), bd=10)
        self.entry.pack(side="left", fill="both", expand=True)
        self.entry.insert(0, "Mumbai")
        self.entry.bind("<Return>", lambda e: self._search())

        tk.Button(ef, text="→", bg=T["blue"], fg=T["bg_deep"],
                  font=("Segoe UI", 14, "bold"), relief="flat", bd=0,
                  padx=12, cursor="hand2",
                  activebackground=T["blue_light"], activeforeground=T["bg_deep"],
                  command=self._search).pack(side="right")

        # °C / °F toggle
        uf = tk.Frame(s, bg=T["bg_card"])
        uf.place(relx=0.06, rely=0.213, relwidth=0.88, height=32)

        self.btn_c = tk.Button(uf, text="°C", font=("Segoe UI", 10, "bold"),
                               relief="flat", bd=0, cursor="hand2",
                               command=lambda: self._set_unit(True))
        self.btn_f = tk.Button(uf, text="°F", font=("Segoe UI", 10, "bold"),
                               relief="flat", bd=0, cursor="hand2",
                               command=lambda: self._set_unit(False))
        self.btn_c.pack(side="left", expand=True, fill="both")
        self.btn_f.pack(side="left", expand=True, fill="both")
        self._refresh_unit_btns()

        # Status
        self.status_var = tk.StringVar(value="Enter city and press →")
        self.status_lbl = tk.Label(s, textvariable=self.status_var,
                                   bg=T["bg_card"], fg=T["text_dim"],
                                   font=("Segoe UI", 8), wraplength=200,
                                   justify="center")
        self.status_lbl.place(relx=0.5, rely=0.258, anchor="n")

        # ── Big weather icon
        self.icon_lbl = tk.Label(s, text="◈", bg=T["bg_card"],
                                 fg=T["blue"], font=("Segoe UI", 72))
        self.icon_lbl.place(relx=0.5, rely=0.3, anchor="n")

        # Big temperature
        self.big_temp = tk.Label(s, text="—", bg=T["bg_card"],
                                 fg=T["text_bright"],
                                 font=("Segoe UI", 60, "bold"))
        self.big_temp.place(relx=0.5, rely=0.445, anchor="n")

        # Condition text
        self.cond_lbl = tk.Label(s, text="—", bg=T["bg_card"],
                                 fg=T["text_muted"], font=("Segoe UI", 13))
        self.cond_lbl.place(relx=0.5, rely=0.565, anchor="n")

        # City
        self.city_lbl = tk.Label(s, text="—", bg=T["bg_card"],
                                 fg=T["text_main"], font=("Segoe UI", 16, "bold"))
        self.city_lbl.place(relx=0.5, rely=0.602, anchor="n")

        # Local time
        self.time_lbl = tk.Label(s, text="—", bg=T["bg_card"],
                                 fg=T["text_dim"], font=("Segoe UI", 9))
        self.time_lbl.place(relx=0.5, rely=0.638, anchor="n")

        # Divider
        tk.Frame(s, bg=T["border"], height=1
                 ).place(relx=0.06, rely=0.672, relwidth=0.88)

        # Mini stat grid (2 cols x 3 rows)
        self._sv = {}
        specs = [
            ("HUMIDITY",   "hum"),
            ("FEELS LIKE", "feels"),
            ("WIND",       "wind"),
            ("UV INDEX",   "uv"),
            ("VISIBILITY", "vis"),
            ("PRESSURE",   "pres"),
        ]
        for i, (label, key) in enumerate(specs):
            col = i % 2
            row = i // 2
            rx = 0.08 + col * 0.47
            ry = 0.688 + row * 0.075

            tk.Label(s, text=label, bg=T["bg_card"], fg=T["text_dim"],
                     font=("Segoe UI", 7, "bold"), anchor="w"
                     ).place(relx=rx, rely=ry)
            v = tk.Label(s, text="—", bg=T["bg_card"], fg=T["text_main"],
                         font=("Segoe UI", 11, "bold"), anchor="w")
            v.place(relx=rx, rely=ry + 0.024)
            self._sv[key] = v

        # Footer
        tk.Label(s, text="powered by weatherapi.com", bg=T["bg_card"],
                 fg=T["text_dim"], font=("Segoe UI", 7)
                 ).place(relx=0.5, rely=0.978, anchor="s")

    # ── CONTENT ────────────────────────────
    def _build_content(self):
        c = self.content

        # Top bar
        topbar = tk.Frame(c, bg=T["bg_main"], height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="TODAY'S OVERVIEW", bg=T["bg_main"],
                 fg=T["text_muted"], font=("Segoe UI", 9, "bold")
                 ).pack(side="left", padx=28, pady=16)

        self.date_lbl = tk.Label(topbar, text="", bg=T["bg_main"],
                                 fg=T["text_dim"], font=("Segoe UI", 9))
        self.date_lbl.pack(side="right", padx=28)

        # ── Summary cards row
        cards_row = tk.Frame(c, bg=T["bg_main"])
        cards_row.pack(fill="x", padx=20, pady=(0, 6))

        self._cards = {}
        card_specs = [
            ("aqi",   "AIR QUALITY", T["cyan"]),
            ("high",  "TODAY HIGH",  T["gold"]),
            ("low",   "TODAY LOW",   T["blue_light"]),
            ("rain",  "RAIN CHANCE", T["rose"]),
        ]
        for key, title, accent in card_specs:
            f = tk.Frame(cards_row, bg=T["bg_card"])
            f.pack(side="left", expand=True, fill="both", padx=5, pady=4)
            tk.Label(f, text=title, bg=T["bg_card"], fg=T["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w"
                     ).pack(anchor="w", padx=16, pady=(12, 0))
            v = tk.Label(f, text="—", bg=T["bg_card"], fg=accent,
                         font=("Segoe UI", 22, "bold"), anchor="w")
            v.pack(anchor="w", padx=16, pady=(0, 12))
            self._cards[key] = v

        # ── Hourly section
        tk.Label(c, text="HOURLY FORECAST", bg=T["bg_main"],
                 fg=T["text_muted"], font=("Segoe UI", 8, "bold")
                 ).pack(anchor="w", padx=28, pady=(8, 4))

        hr_row = tk.Frame(c, bg=T["bg_main"])
        hr_row.pack(fill="x", padx=20, pady=(0, 6))

        self._hcells = []
        for _ in range(8):
            f = tk.Frame(hr_row, bg=T["bg_card"])
            f.pack(side="left", expand=True, fill="both", padx=4)
            hl = tk.Label(f, text="—", bg=T["bg_card"], fg=T["text_dim"],
                          font=("Segoe UI", 8))
            hl.pack(pady=(10, 0))
            il = tk.Label(f, text="◈", bg=T["bg_card"], fg=T["blue"],
                          font=("Segoe UI", 18))
            il.pack()
            tl = tk.Label(f, text="—", bg=T["bg_card"], fg=T["text_bright"],
                          font=("Segoe UI", 11, "bold"))
            tl.pack(pady=(0, 10))
            self._hcells.append((hl, il, tl))

        # ── 7-day forecast section
        tk.Label(c, text="7-DAY FORECAST", bg=T["bg_main"],
                 fg=T["text_muted"], font=("Segoe UI", 8, "bold")
                 ).pack(anchor="w", padx=28, pady=(8, 4))

        fc_outer = tk.Frame(c, bg=T["bg_main"])
        fc_outer.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        self._fc_rows = []
        for i in range(7):
            row = tk.Frame(fc_outer, bg=T["bg_card"])
            row.pack(fill="x", pady=3, padx=4, ipady=8)

            day_l = tk.Label(row, text="—", bg=T["bg_card"], fg=T["text_main"],
                             font=("Segoe UI", 11, "bold"), width=11, anchor="w")
            day_l.pack(side="left", padx=18)

            ico_l = tk.Label(row, text="◈", bg=T["bg_card"], fg=T["blue"],
                             font=("Segoe UI", 15), width=3)
            ico_l.pack(side="left", padx=6)

            cond_l = tk.Label(row, text="—", bg=T["bg_card"], fg=T["text_muted"],
                              font=("Segoe UI", 10), anchor="w")
            cond_l.pack(side="left", expand=True, fill="x")

            rain_l = tk.Label(row, text="", bg=T["bg_card"], fg=T["blue"],
                              font=("Segoe UI", 9), width=9, anchor="e")
            rain_l.pack(side="right", padx=8)

            hi_l = tk.Label(row, text="—", bg=T["bg_card"], fg=T["gold"],
                            font=("Segoe UI", 11, "bold"), width=6, anchor="e")
            hi_l.pack(side="right")

            lo_l = tk.Label(row, text="—", bg=T["bg_card"], fg=T["blue_light"],
                            font=("Segoe UI", 11), width=6, anchor="e")
            lo_l.pack(side="right")

            self._fc_rows.append((day_l, ico_l, cond_l, hi_l, lo_l, rain_l))

    # ── SEARCH ─────────────────────────────
    def _search(self):
        city = self.entry.get().strip()
        if city:
            self._do_search(city)

    def _do_search(self, city):
        self._set_status("Fetching weather…", T["text_muted"])
        self.root.update()
        threading.Thread(target=self._fetch_thread, args=(city,), daemon=True).start()

    def _fetch_thread(self, city):
        try:
            raw = fetch_forecast(city, days=7)
            w, fc, hr = parse_data(raw)
            self._w, self._fc, self._hr = w, fc, hr
            self.root.after(0, self._render)
        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self._set_status("No internet connection", T["rose"]))
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 0
            msg = {400: "City not found", 401: "Invalid API key — check API_KEY"}.get(code, f"HTTP {code}")
            self.root.after(0, lambda: self._set_status(msg, T["rose"]))
        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Error: {e}", T["rose"]))

    # ── RENDER ─────────────────────────────
    def _render(self):
        if not self._w:
            return
        w  = self._w
        fc = self._fc
        hr = self._hr
        c  = self.celsius
        unit = "°C" if c else "°F"

        # Sidebar
        ico, col = get_visual(w["condition"])
        self.icon_lbl.config(text=ico, fg=col)
        temp  = w["temp_c"] if c else w["temp_f"]
        feels = w["feels_c"] if c else w["feels_f"]
        self.big_temp.config(text=f"{temp:.0f}{unit}")
        self.cond_lbl.config(text=w["condition"])
        self.city_lbl.config(text=f"{w['city']}, {w['country']}")
        self.time_lbl.config(text=w["localtime"])

        self._sv["hum"].config(  text=f"{w['humidity']}%")
        self._sv["feels"].config(text=f"{feels:.0f}{unit}")
        self._sv["wind"].config( text=f"{w['wind_kph']} km/h")
        self._sv["uv"].config(   text=str(w["uv"]))
        self._sv["vis"].config(  text=f"{w['vis_km']} km")
        self._sv["pres"].config( text=f"{w['pressure']} mb")
        self._set_status(f"Updated {w['localtime']}", T["text_dim"])

        # Date
        try:
            dt = datetime.strptime(w["localtime"], "%Y-%m-%d %H:%M")
            self.date_lbl.config(text=dt.strftime("%A, %B %d %Y"))
        except Exception:
            pass

        # Summary cards
        today = fc[0] if fc else None
        if today:
            hi = today["max_c"] if c else today["max_f"]
            lo = today["min_c"] if c else today["min_f"]
            self._cards["high"].config(text=f"{hi:.0f}{unit}")
            self._cards["low"].config( text=f"{lo:.0f}{unit}")
            self._cards["rain"].config(text=f"{today['rain_pct']}%")
        self._cards["aqi"].config(text=w["aqi"])

        # Hourly
        for i, (hl, il, tl) in enumerate(self._hcells):
            if i < len(hr):
                h = hr[i]
                t = h["temp_c"] if c else h["temp_f"]
                ico2, col2 = get_visual(h["cond"])
                hl.config(text=h["hour"])
                il.config(text=ico2, fg=col2)
                tl.config(text=f"{t:.0f}°")
            else:
                hl.config(text=""); il.config(text=""); tl.config(text="")

        # 7-day
        for i, (day_l, ico_l, cond_l, hi_l, lo_l, rain_l) in enumerate(self._fc_rows):
            if i < len(fc):
                d = fc[i]
                hi = d["max_c"] if c else d["max_f"]
                lo = d["min_c"] if c else d["min_f"]
                ico3, col3 = get_visual(d["condition"])
                day_l.config( text="Today" if i == 0 else d["day"])
                ico_l.config( text=ico3, fg=col3)
                cond_l.config(text=d["condition"])
                hi_l.config(  text=f"{hi:.0f}°")
                lo_l.config(  text=f"{lo:.0f}°")
                rain_l.config(text=f"🌧 {d['rain_pct']}%" if d["rain_pct"] > 0 else "")

    # ── HELPERS ────────────────────────────
    def _set_unit(self, use_c):
        self.celsius = use_c
        self._refresh_unit_btns()
        if self._w:
            self._render()

    def _refresh_unit_btns(self):
        if self.celsius:
            self.btn_c.config(bg=T["blue"],     fg=T["bg_deep"],   activebackground=T["blue_light"])
            self.btn_f.config(bg=T["bg_input"], fg=T["text_muted"],activebackground=T["bg_hover"])
        else:
            self.btn_f.config(bg=T["blue"],     fg=T["bg_deep"],   activebackground=T["blue_light"])
            self.btn_c.config(bg=T["bg_input"], fg=T["text_muted"],activebackground=T["bg_hover"])

    def _set_status(self, msg, color=None):
        self.status_var.set(msg)
        if color:
            self.status_lbl.config(fg=color)


# ══════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = SkyeWeather(root)
    root.mainloop()
