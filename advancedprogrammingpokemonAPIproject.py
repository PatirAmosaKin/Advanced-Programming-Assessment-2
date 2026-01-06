import tkinter as tk
from tkinter import messagebox
import requests, tempfile, subprocess, sys, os
from PIL import Image, ImageTk, ImageEnhance
from io import BytesIO

# ---------- CONSTANTS ----------
FOOTER_IMAGE_PATH = "International_Pokémon_logo.svg.png"
URL = "https://pokeapi.co/api/v2/pokemon/"

TYPE_CHART = {
    "fire": {"grass": 2, "ice": 2, "bug": 2, "steel": 2},
    "water": {"fire": 2, "ground": 2, "rock": 2},
    "grass": {"water": 2, "ground": 2, "rock": 2},
    "electric": {"water": 2, "flying": 2, "ground": 0},
    "ground": {"fire": 2, "electric": 2, "rock": 2, "steel": 2},
    "fighting": {"normal": 2, "ice": 2, "rock": 2, "steel": 2, "dark": 2, "ghost": 0},
    "psychic": {"fighting": 2, "poison": 2, "dark": 0},
    "poison": {"grass": 2, "fairy": 2, "ground": 0.5, "psychic": 0.5, "steel": 0},
    "ice": {"grass": 2, "ground": 2, "flying": 2, "dragon": 2},
    "dragon": {"dragon": 2},
    "ghost": {"psychic": 2, "ghost": 2, "normal": 0},
    "dark": {"psychic": 2, "ghost": 2},
    "rock": {"fire": 2, "ice": 2, "flying": 2, "bug": 2},
    "steel": {"ice": 2, "rock": 2, "fairy": 2},
    "fairy": {"fighting": 2, "dragon": 2, "dark": 2}
}

# ---------- UI & Stuff ----------
def title_box(parent, text):
    box = tk.Frame(parent, bg="#f0f0f0", bd=2, relief="groove")
    box.pack(fill="x", padx=20, pady=(10, 5))
    tk.Label(box, text=text, font=("Arial", 14, "bold"), bg="#f0f0f0").pack(pady=5)

def get_pokemon(name):
    try:
        return requests.get(URL + name.lower()).json()
    except:
        return None

def base_stat_total(p):
    return sum(s["base_stat"] for s in p["stats"])

def type_multiplier(a, d):
    mult = 1
    for atk in a:
        for dfn in d:
            mult *= TYPE_CHART.get(atk, {}).get(dfn, 1)
    return mult

def predict_winner(p1, p2):
    t1 = [t["type"]["name"] for t in p1["types"]]
    t2 = [t["type"]["name"] for t in p2["types"]]
    b1, b2 = base_stat_total(p1), base_stat_total(p2)
    e1, e2 = type_multiplier(t1, t2), type_multiplier(t2, t1)

    if abs(b1 - b2) >= 200:
        return (p1 if b1 > b2 else p2), "Much higher base stats"
    if e1 != e2:
        return (p1 if e1 > e2 else p2), "Type advantage"
    return (p1 if b1 > b2 else p2), "Higher base stats"

def load_image(url, fade=False):
    img = Image.open(BytesIO(requests.get(url).content)).convert("RGB")
    img = img.resize((90, 90))
    if fade:
        img = ImageEnhance.Brightness(img).enhance(0.4)
    return ImageTk.PhotoImage(img)

# ---------- AUDIO ----------
def play_cry(pokemon):
    try:
        audio = requests.get(pokemon["cries"]["latest"]).content
        f = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        f.write(audio); f.close()

        cmd = ["afplay", f.name] if sys.platform == "darwin" else ["aplay", f.name]
        subprocess.Popen(cmd)
    except:
        pass

def bind_cry(widget, pokemon):
    widget.bind("<Button-1>", lambda _: play_cry(pokemon))

# ---------- ROOT ----------
root = tk.Tk()
root.title("Pokémon Analyzer")
root.geometry("450x450")
root.resizable(False, False)

content = tk.Frame(root)
content.pack(fill="both", expand=True, pady=(0, 40))

footer = tk.Frame(root, height=40)
footer.pack(fill="x", side="bottom")

logo_raw = Image.open(FOOTER_IMAGE_PATH)
logo_raw = logo_raw.resize((int(logo_raw.width * 0.09375), int(logo_raw.height * 0.09375)))
logo = ImageTk.PhotoImage(logo_raw)
tk.Label(footer, image=logo).pack(pady=2)

# ---------- VARIABLES ----------
p1_var, p2_var, stats_var = tk.StringVar(), tk.StringVar(), tk.StringVar()

# ---------- NAV ----------
def show(frame):
    frame.tkraise()

# ---------- FRAMES ----------
def make_button(parent, text, cmd):
    tk.Button(parent, text=text, command=cmd).pack(pady=3)

main_menu = tk.Frame(content)
title_box(main_menu, "Pokémon Analyzer")
make_button(main_menu, "Start", lambda: show(start_menu))
make_button(main_menu, "Instructions", lambda: show(instructions))
make_button(main_menu, "Exit", root.destroy)

instructions = tk.Frame(content)
title_box(instructions, "Instructions")
tk.Label(
    instructions,
    text="• Predict battle winners\n• View Pokémon stats\n• Click images to hear cries\n\nPowered by PokéAPI",
    justify="left"
).pack(padx=10)
make_button(instructions, "Back", lambda: show(main_menu))

start_menu = tk.Frame(content)
title_box(start_menu, "Catch 'em all!")
make_button(start_menu, "Battle Predictor", lambda: show(battle_1))
make_button(start_menu, "Stats Comparison", lambda: show(stats_1))
make_button(start_menu, "Back", lambda: show(main_menu))

# ---------- BATTLE ----------
battle_1 = tk.Frame(content)
title_box(battle_1, "Battle Predictor")
tk.Label(battle_1, text="Pokémon 1").pack()
tk.Entry(battle_1, textvariable=p1_var).pack()
tk.Label(battle_1, text="Pokémon 2").pack()
tk.Entry(battle_1, textvariable=p2_var).pack()

battle_2 = tk.Frame(content)
result = tk.Label(battle_2, font=("Arial", 12))
result.pack()

img_frame = tk.Frame(battle_2)
img_frame.pack()

img1, img2 = tk.Label(img_frame), tk.Label(img_frame)
img1.grid(row=0, column=0, padx=10)
img2.grid(row=0, column=1, padx=10)

def run_battle():
    p1, p2 = get_pokemon(p1_var.get()), get_pokemon(p2_var.get())
    if not p1 or not p2:
        messagebox.showerror("Error", "Invalid Pokémon")
        return

    winner, reason = predict_winner(p1, p2)
    for lbl, p in ((img1, p1), (img2, p2)):
        img = load_image(p["sprites"]["front_default"], winner != p)
        lbl.config(image=img); lbl.image = img
        bind_cry(lbl, p)

    result.config(text=f"{winner['name'].capitalize()} wins\n{reason}")
    show(battle_2)

make_button(battle_1, "Predict", run_battle)
make_button(battle_1, "Back", lambda: show(start_menu))
make_button(battle_2, "Back", lambda: show(battle_1))

# ---------- STATS ----------
stats_1 = tk.Frame(content)
title_box(stats_1, "Stats")
tk.Entry(stats_1, textvariable=stats_var).pack()

stats_2 = tk.Frame(content)
stats_img, stats_text = tk.Label(stats_2), tk.Label(stats_2, justify="left")
stats_img.pack(); stats_text.pack()

def show_stats(name):
    p = get_pokemon(name)
    if not p:
        messagebox.showerror("Error", "Invalid Pokémon")
        return

    img = load_image(p["sprites"]["front_default"])
    stats_img.config(image=img); stats_img.image = img
    bind_cry(stats_img, p)

    stats_text.config(text="\n".join(
        [p["name"].capitalize()] + 
        [f"{s['stat']['name']}: {s['base_stat']}" for s in p["stats"]]
    ))
    show(stats_2)

make_button(stats_1, "Show Stats", lambda: show_stats(stats_var.get()))
make_button(stats_1, "Back", lambda: show(start_menu))
make_button(stats_2, "Back", lambda: show(stats_1))

# ---------- PLACE FRAMES ----------
for f in (main_menu, instructions, start_menu, battle_1, battle_2, stats_1, stats_2):
    f.place(relwidth=1, relheight=1)

show(main_menu)
root.mainloop()
