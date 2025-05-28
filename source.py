import os
import sys
import time
import webbrowser
import discord
import re
import requests
import urllib.parse
import json
import logging
import threading
import tkinter as tk
# logging.basicConfig(level=logging.INFO)
from discord.ext import commands
transparencyshift = 0
h = False
c = False
print(f"By \033[94m.lunary. on dicsord blah blah blah")
"""IF YOU'RE USING .PY VERSION MAKE SURE TO GET ALL THE IMPORTS WITH PIP. (pip install requests for example) """

def get_base_path():
    if getattr(sys, 'frozen', False):  # Running as .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:  # Running as .py
        return os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(get_base_path(), 'config.json')

try:
    with open(config_path, 'r') as f:
        config = json.load(f)
except Exception as e:
    print(f"Failed to load config.json: {e}")
    sys.exit()
    
GlitchEnabled = config.get("GlitchEnabled", True)
DreamspaceEnabled = config.get("DreamspaceEnabled", True)
token = config.get("discordToken", "")
robloxCookie = config.get("robloxCookie", "")


if token  == "":
    print("No discord token provided")
    time.sleep(3)
    sys.exit()
    
def format_keywords(keywords):
    return [keyword.replace("<space>", " ") for keyword in keywords]

def convert_to_deeplink(link: str) -> str | None:
    # Regex to match share link with code param
    regex_share = re.compile(r"https:\/\/www\.roblox\.com/share\?code=([a-zA-Z0-9]+)")
    # Regex to match game link with optional privateServerLinkCode param
    regex_private = re.compile(
        r"https:\/\/www\.roblox\.com/games/15532962292(?:\/[^\s?]+)?(?:\?privateServerLinkCode=([a-zA-Z0-9]+))?"
    )

    match_share = regex_share.match(link)
    match_private = regex_private.match(link)

    if match_share:
        access_code = match_share.group(1)
        deeplink = (
            f"roblox://navigation/share_links?code={access_code}&type=Server&pid=share&is_retargeting=true"
        )
        print("Converted share link")
        return deeplink

    if match_private:
        access_code = match_private.group(1)  # can be None if no privateServerLinkCode param
        if access_code is None:
            access_code = ""
        deeplink = f"roblox://placeID=15532962292&linkCode={access_code}"
        print("Converted private server link")
        return deeplink

    print(f"Invalid link: {link}")
    return None

def extract_share_code(url: str) -> str | None:
    match = re.search(r'https:\/\/www\.roblox\.com\/share\?code=([a-zA-Z0-9]+)', url)
    if match:
        return match.group(1)
    return None

def fetch_keywords(url):
    def clean_keywords(keywords):
        return [kw.replace("<space>", " ") for kw in keywords]

    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse the raw text as JSON manually
        data = json.loads(response.text)

        GKeywords = clean_keywords(data.get("requiredG", []))
        DKeywords = clean_keywords(data.get("requiredD", []))
        IKeywords = clean_keywords(data.get("ignoreKeywords", []))

        return GKeywords, DKeywords, IKeywords

    except Exception as e:
        print(f"Error fetching or parsing keywords: {e}")
        return [], [], []


# Usage
url = "https://raw.githubusercontent.com/Lunatic-T/Websniper/refs/heads/main/Keywords.json"
GKeywords, DKeywords, IKeywords = fetch_keywords(url)

# print("GKeywords:", GKeywords)
# print("DKeywords:", DKeywords)
# print("IKeywords:", IKeywords)

bot = commands.Bot("", self_bot=True)

@bot.event
async def on_ready():
    print(f"\033[94mStarted bot")

@bot.event
async def on_message(message: discord.Message):
    global h
    if h == False:
        return
    if message.guild is None:
        return

    if message.guild.id != 1186570213077041233: #1186570213077041233 -sols rng server id
        return

    if message.channel.id != 1282542323590496277: #1282542323590496277 -sols rng biomes channel id
        return

    content = message.content
    # Ignore message if it contains any ignore keyword
    if any(ignore_kw.lower() in content.lower() for ignore_kw in IKeywords):
        return
    urls = re.findall(r'https?://\S+', content)
    if not urls:
        return
    
    # Check if message contains any required keyword from G or D lists
    matched_keyword = None
    for kw in GKeywords:
        if kw.lower() in content.lower():
            matched_keyword = kw
            if GlitchEnabled:
                break
            else:
                matched_keyword = None

    # If no G keyword matched or G disabled, check D keywords
    if matched_keyword is None:
        for kw in DKeywords:
            if kw.lower() in content.lower():
                matched_keyword = kw
                if DreamspaceEnabled:
                    break
                else:
                    matched_keyword = None

    if matched_keyword is None:
        return
        
    print("\n\033[91m-----------------------------------------------------------------\033[0m\n")
    print(f"\033[92m{content}")
    url = urls[0]
    print(url)
    webbrowser.open(convert_to_deeplink(url))
    print("\033[92mjoined instantly, leaving if fake")
    if extract_share_code(urls[0]):
        start = time.perf_counter()
        SHARE_LINK_CODE = extract_share_code(urls[0])
        
        csrf_req = requests.post(
            "https://auth.roblox.com/v1/logout",
            cookies={".ROBLOSECURITY": robloxCookie}
        )
        x_csrf_token = csrf_req.headers.get("x-csrf-token")
        
        if not x_csrf_token:
            print("Failed to get CSRF token. Check if your Roblox cookie is valid or try again later if it is rate-limited.")
            return
        
        res = requests.post(
            "https://apis.roblox.com/sharelinks/v1/resolve-link",
            headers={"x-csrf-token": x_csrf_token, "Content-Type": "application/json"},
            cookies={".ROBLOSECURITY": robloxCookie},
            json={"linkId": SHARE_LINK_CODE, "linkType": "Server"}
        )
        # Step 3: Get the placeId and gameInstanceId
        if res.ok:
            data = res.json()
            i = data.get("privateServerInviteData")
            if not i:
                print("\033[91mCould not find privateServerInviteData in response.")
                print(f"\033[91m{res.text}")
                return
            param1 = i.get("placeId")
            param2 = i.get("ownerUserId")
            param3 = i.get("linkCode")
            print(f"\033[90m{data}")
            if str(param1).strip() == "15532962292":
                print(f'\033[92mgameid: {param1}')
            else:
                print(f'\033[91mgameid: {param1}')
            
            print(f'\033[92mprivate server owner: {param2}')
            print(f'\033[92mprivateserverlink: {param3}')
        else:
            print(f"\033[91mError: {res.status_code}{res.text}")
            input("press enter to continue")

    if str(param1).strip() == "15532962292":
        end = time.perf_counter()
        dur = end - start
        if dur < 0.75:
            print(f"Took: \033[92m{dur:.4f}\033[0m seconds to verify gameid")  # green
        else:
            print(f"Took: \033[91m{dur:.4f}\033[0m seconds to verify gameid")  # red
        print(f"\033[92opened with matched keyword: \033[93m'{matched_keyword}' at link \033[95m'{url}'")
        print("\n\033[91m-----------------------------------------------------------------\033[0m\n")
    else:
        urlsafe = "https://www.roblox.com/games/15532962292?privateServerLinkCode=84851469547452852766157119385988"
        webbrowser.open(convert_to_deeplink(urlsafe))
        print(f"\033[91m!! REDIRECTING TO A SAFE SOLS RNG PRIVATE SERVER TO PREVENT JOINING A NON SOL'S RNG GAME. !!")
        print("\n\033[91m-----------------------------------------------------------------\033[0m\n")
        
        
def start_bot():
    try:
        bot.run(token, bot=False)
    except Exception as e:
        print(f"Bot error: {e}")

# ---------- Tkinter GUI setup ---------- 

def toggle():
    global h
    global c
    if not c:
        c = True
        threading.Thread(target=start_bot, daemon=True).start()  # ✅ run bot in background
    if h:
        h = False
        toggle_button.config(text="Stopped")
        print(f"\033[94mStopped Message detection")
    else:
        h = True
        toggle_button.config(text="Running")
        print(f"\033[94mStarted Message detection")

def start_move(event):
    root._drag_start_x = event.x_root
    root._drag_start_y = event.y_root

def do_move(event):
    dx = event.x_root - root._drag_start_x
    dy = event.y_root - root._drag_start_y
    x = root.winfo_x() + dx
    y = root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")
    root._drag_start_x = event.x_root
    root._drag_start_y = event.y_root


def toggle_transparency():
    global transparencyshift
    transparency_levels = [1, 0.75, 0.5, 0.25]
    
    transparencyshift = (transparencyshift + 1) % len(transparency_levels)
    root.attributes('-alpha', transparency_levels[transparencyshift])

root = tk.Tk()
root.geometry('247x24+50+50')
root.resizable(False, False)
root.attributes('-topmost', 1)
root.overrideredirect(True)
root.title("AntiIdle")

frame = tk.Frame(root, bg="gray20", height=30)
frame.pack(fill=tk.BOTH, expand=True)
frame.bind("<Button-1>", start_move)
frame.bind("<B1-Motion>", do_move)

close_btn = tk.Button(frame, text="X", command=root.destroy, bg="#222", fg="white", bd=0, font=("Segoe UI", 10, "bold"), takefocus=0, highlightthickness=0)
close_btn.place(x=203, y=2, width=20, height=20)

toggle_button = tk.Button(
    frame,
    text="Start sniping",
    command=toggle,
    bg="#222",           
    fg="white",          
    activebackground="#444",  
    activeforeground="white",
    highlightthickness=0,
    bd=0,
    takefocus=0,              
    font=("Segoe UI", 10, "bold"),
    relief="flat",       
    cursor="hand2"
)
toggle_button.place(x=2, y=2,width=177, height=20)

# Transparency toggle button
transparency_button = tk.Button(
    frame,
    text="I",
    command=toggle_transparency,
    width=20,
    height=2,
    bg="#222",           
    fg="white",          
    activebackground="#444",  
    activeforeground="white",
    highlightthickness=0,
    bd=0,
    takefocus=0,             
    font=("Segoe UI", 10, "bold"),
    relief="flat",       
    cursor="hand2"
)
transparency_button.place(x=181, y=2, width=20, height=20)

def on_transparency_button_enter(e):
    transparency_button.config(bg="#444", fg="white")

def on_transparency_button_leave(e):
    transparency_button.config(bg="#222", fg="white")

# Hover effects for the toggle button
def on_toggle_button_enter(e):
    toggle_button.config(bg="#444", fg="white")

def on_toggle_button_leave(e):
    toggle_button.config(bg="#222", fg="white")

# Hover effects for the close button
def on_close_button_enter(e):
    close_btn.config(bg="#444", fg="white")

def on_close_button_leave(e):
    close_btn.config(bg="#222", fg="white")

# Bind hover effects to buttons
transparency_button.bind("<Enter>", on_transparency_button_enter)
transparency_button.bind("<Leave>", on_transparency_button_leave)

toggle_button.bind("<Enter>", on_toggle_button_enter)
toggle_button.bind("<Leave>", on_toggle_button_leave)

close_btn.bind("<Enter>", on_close_button_enter)
close_btn.bind("<Leave>", on_close_button_leave)


# Run the GUI
root.mainloop()
# ---------- Tkinter GUI setup ---------- 


""" if i got you into glitch biome, put a star at https://github.com/Lunatic-T/PySniper!"""
