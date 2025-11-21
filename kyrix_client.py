import tkinter as tk
import time
import psutil
import pyautogui
import keyboard
import win32gui
import win32process
import threading
from pynput import keyboard as pk
from pynput import mouse as pm

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

_MOUSE_BUTTON_TO_NAME = {
    pm.Button.x1: "MBUTTON1",
    pm.Button.x2: "MBUTTON2",
    pm.Button.middle: "MBUTTON3",
}

def safe_upper_key_from_pynput(key):
    try:
        if isinstance(key, pk.KeyCode):
            if key.char is None:
                return None
            return key.char.upper()
        else:
            name = str(key).split(".")[-1]
            return name.upper()
    except Exception:
        return None

class ThrowpotCard(tk.Frame):
    def __init__(self, parent, card_id, remove_callback, app_reference):
        super().__init__(parent, bg="#1e1e2e", highlightbackground="#2e2e3e", highlightthickness=2)
        self.card_id = card_id
        self.remove_callback = remove_callback
        self.app = app_reference
        self.enabled = False
        self.delay = 100
        self.return_slot = 1
        self.click_slot = 1
        self.keybind = None
        self.is_listening = False

        self._executing = False
        self._exec_lock = threading.Lock()

        self.config(width=400, height=500)
        self.pack_propagate(False)
        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self, bg="#1e1e2e")
        header.pack(fill="x", padx=15, pady=10)

        tk.Label(header, text="Aktif Et", font=("Arial", 11, "bold"),
                 fg="white", bg="#1e1e2e").pack(side="left")

        close_btn = tk.Button(header, text="×", font=("Arial", 16),
                              fg="#888", bg="#1e1e2e", bd=0,
                              activebackground="#2e2e3e", activeforeground="white",
                              command=lambda: self.remove_callback(self.card_id))
        close_btn.pack(side="right", padx=5)

        self.toggle_frame = tk.Frame(header, bg="#444", width=50, height=24)
        self.toggle_frame.pack(side="right")
        self.toggle_frame.pack_propagate(False)

        self.toggle_circle = tk.Label(self.toggle_frame, text="", bg="#666", width=2)
        self.toggle_circle.place(x=2, y=2)
        self.toggle_frame.bind("<Button-1>", lambda e: self.toggle_enabled())

        delay_frame = tk.Frame(self, bg="#1e1e2e")
        delay_frame.pack(fill="x", padx=15, pady=10)

        delay_label = tk.Label(delay_frame, text="Delay", font=("Arial", 10),
                               fg="white", bg="#1e1e2e")
        delay_label.pack(side="left")

        self.delay_value = tk.Label(delay_frame, text=f"{self.delay}ms",
                                    font=("Arial", 10, "bold"),
                                    fg="#a855f7", bg="#1e1e2e")
        self.delay_value.pack(side="right")

        self.delay_slider = tk.Scale(delay_frame, from_=100, to=500,
                                     orient="horizontal", bg="#1e1e2e",
                                     fg="#a855f7", troughcolor="#2e2e3e",
                                     highlightthickness=0, bd=0,
                                     showvalue=0, activebackground="#a855f7",
                                     command=self._on_delay_command)
        self.delay_slider.set(self.delay)
        self.delay_slider.pack(fill="x", pady=5)

        self.create_slot_section("Return Slot", "return")
        self.create_slot_section("Click Slot", "click")

        keybind_frame = tk.Frame(self, bg="#1e1e2e")
        keybind_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(keybind_frame, text="Tuş Atama", font=("Arial", 10),
                 fg="white", bg="#1e1e2e").pack(anchor="w")

        self.keybind_btn = tk.Button(keybind_frame, text="Tuş Ata",
                                     font=("Arial", 12, "bold"),
                                     bg="#2e2e3e", fg="#888", bd=0,
                                     activebackground="#3e3e4e",
                                     height=2, command=self.start_listening)
        self.keybind_btn.pack(fill="x", pady=5)

    def _on_delay_command(self, v):
        try:
            self.delay = int(float(v))
            self.delay_value.config(text=f"{self.delay}ms")
        except Exception:
            pass

    def create_slot_section(self, title, slot_type):
        frame = tk.Frame(self, bg="#1e1e2e")
        frame.pack(fill="x", padx=15, pady=10)

        tk.Label(frame, text=title, font=("Arial", 10),
                 fg="white", bg="#1e1e2e").pack(anchor="w")

        buttons_frame = tk.Frame(frame, bg="#1e1e2e")
        buttons_frame.pack(fill="x", pady=5)

        slot_buttons = []
        for i in range(1, 10):
            btn = tk.Button(buttons_frame, text=str(i),
                            font=("Arial", 10), width=4, height=1,
                            bg="#2e2e3e", fg="white", bd=0,
                            activebackground="#a855f7")
            btn.pack(side="left", padx=2, expand=True, fill="x")
            btn.config(command=lambda b=btn, n=i, t=slot_type: self.select_slot(b, n, t, slot_buttons))
            slot_buttons.append(btn)

        if slot_type == "return":
            self.return_buttons = slot_buttons
            slot_buttons[0].config(bg="#a855f7")
        else:
            self.click_buttons = slot_buttons
            slot_buttons[0].config(bg="#a855f7")

    def select_slot(self, button, number, slot_type, all_buttons):
        for btn in all_buttons:
            btn.config(bg="#2e2e3e")
        button.config(bg="#a855f7")

        if slot_type == "return":
            self.return_slot = number
        else:
            self.click_slot = number

    def toggle_enabled(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.toggle_circle.config(bg="#a855f7")
            self.toggle_circle.place(x=26, y=2)
            self.toggle_frame.config(bg="#a855f7")
        else:
            self.toggle_circle.config(bg="#666")
            self.toggle_circle.place(x=2, y=2)
            self.toggle_frame.config(bg="#444")

    def start_listening(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.after(0, lambda: self.keybind_btn.config(text="Dinleniyor... (ESC iptal)", bg="#a855f7", fg="white"))

    def assign_keybind_from_event(self, name):
        if not self.is_listening:
            return False

        if name == "ESC":
            self.keybind = None
            self.is_listening = False
            self.after(0, lambda: self.keybind_btn.config(text="Tuş Ata", bg="#2e2e3e", fg="#888"))
            return True

        if name.startswith("MBUTTON"):
            try:
                idx = int(name.replace("MBUTTON", ""))
                if 1 <= idx <= 4:
                    self.keybind = name
                    self.is_listening = False
                    self.after(0, lambda: self.keybind_btn.config(text=name, bg="#2e2e3e", fg="white"))
                    return True
            except Exception:
                return False
        else:
            if name in ("LEFT", "RIGHT", "LBUTTON", "RBUTTON"):
                return False
            self.keybind = name
            self.is_listening = False
            self.after(0, lambda: self.keybind_btn.config(text=name, bg="#2e2e3e", fg="white"))
            return True

        return False

    def in_game(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            p = psutil.Process(pid)
            return (p.name() or "").lower() == "sonoyuncuclient.exe"
        except Exception:
            return False

    def try_start_execution(self):
        locked = self._exec_lock.acquire(blocking=False)
        if not locked:
            return False
        self._executing = True
        return True

    def _run_execute(self):
        try:
            suppress_duration = max(0.15, self.delay / 1000.0 + 0.25)
            self.app.set_suppress(suppress_duration)

            now = time.time()
            last_key = self.app._last_physical_key_name
            last_time = self.app._last_physical_key_time
            skip_click_slot_press = False
            # Eğer kullanıcı yakın zamanda click_slot'a denk gelen bir fiziksel tuşa bastıysa, basımı atla
            if last_key and last_time and now - last_time < 0.35:
                try:
                    if last_key == str(self.click_slot):
                        skip_click_slot_press = True
                except Exception:
                    pass

            if not skip_click_slot_press:
                keyboard.press(str(self.click_slot))
                time.sleep(0.02)
                keyboard.release(str(self.click_slot))

            time.sleep(0.05)

            pyautogui.mouseDown(button="right")
            time.sleep(0.03)
            pyautogui.mouseUp(button="right")

            time.sleep(self.delay / 1000.0)

            keyboard.press(str(self.return_slot))
            time.sleep(0.02)
            keyboard.release(str(self.return_slot))

        except Exception as e:
            try:
                print(f"Hata execute_throwpot: {e}")
            except Exception:
                pass
        finally:
            try:
                self._executing = False
                self._exec_lock.release()
            except Exception:
                pass

    def start_execute_thread(self):
        if not self.try_start_execution():
            return False
        # set immediate suppress to close race window before thread runs
        immediate_suppress = max(0.2, self.delay / 1000.0 + 0.25)
        self.app.set_suppress(immediate_suppress)
        t = threading.Thread(target=self._run_execute, daemon=True)
        t.start()
        return True

class KyrixClient:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Kyrix Client")

        window_width = 900
        window_height = 700
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(False, False)
        self.window.configure(bg="#0a0a0f")

        self.cards = []
        self.next_id = 1

        self.k_listener = None
        self.m_listener = None
        self._running = True
        self._suppress_until = 0.0
        self._suppress_lock = threading.Lock()
        self._last_trigger_times = {}
        self._min_trigger_interval = 0.12

        # last physical key info to avoid double-press problems
        self._last_physical_key_name = None
        self._last_physical_key_time = 0.0

        self.setup_ui()
        self.setup_keybinds()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        header = tk.Frame(self.window, bg="#0a0a0f")
        header.pack(fill="x", padx=20, pady=20)

        title = tk.Label(header, text="Kyrix Client",
                         font=("Arial", 28, "bold"),
                         fg="#a855f7", bg="#0a0a0f")
        title.pack(side="left")

        add_btn = tk.Button(header, text="+ Throwpot Ekle",
                            font=("Arial", 11, "bold"),
                            bg="#a855f7", fg="white", bd=0,
                            activebackground="#9333ea",
                            padx=20, pady=10,
                            command=self.add_throwpot)
        add_btn.pack(side="right")

        container = tk.Frame(self.window, bg="#0a0a0f")
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        canvas = tk.Canvas(container, bg="#0a0a0f", highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg="#0a0a0f")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas = canvas
        self.grid_frame = tk.Frame(self.scrollable_frame, bg="#0a0a0f")
        self.grid_frame.pack(padx=10, pady=10)

        self.empty_label = tk.Label(self.scrollable_frame,
                                    text="Henüz throwpot eklemediniz.\nBaşlamak için yukarıdaki butona tıklayın.",
                                    font=("Arial", 12), fg="#666", bg="#0a0a0f")
        self.empty_label.pack(pady=100)

    def add_throwpot(self):
        if len(self.cards) >= 5:
            return
        self.empty_label.pack_forget()
        card = ThrowpotCard(self.grid_frame, self.next_id, self.remove_throwpot, app_reference=self)
        row = len(self.cards) // 2
        col = len(self.cards) % 2
        card.grid(row=row, column=col, padx=10, pady=10)
        self.cards.append(card)
        self.next_id += 1

    def remove_throwpot(self, card_id):
        for card in list(self.cards):
            if card.card_id == card_id:
                card.destroy()
                self.cards.remove(card)
                break
        for i, card in enumerate(self.cards):
            row = i // 2
            col = i % 2
            card.grid(row=row, column=col, padx=10, pady=10)
        if len(self.cards) == 0:
            self.empty_label.pack(pady=100)

    def set_suppress(self, duration_secs):
        with self._suppress_lock:
            self._suppress_until = max(self._suppress_until, time.time() + duration_secs)

    def is_suppressed(self):
        with self._suppress_lock:
            return time.time() < self._suppress_until

    def setup_keybinds(self):
        def on_key_press(key):
            if not self._running:
                return False
            name = safe_upper_key_from_pynput(key)
            if not name:
                return
            # record last physical key if not suppressed (helps avoid double-press issues)
            if not self.is_suppressed():
                self._last_physical_key_name = name
                self._last_physical_key_time = time.time()
            # if suppressed, ignore
            if self.is_suppressed():
                return
            # only act if Sonoyuncu is foreground
            # (extra safety: ensure event only triggers when game active)
            # If no cards, skip
            if not any(self.cards):
                return
            # assignment mode
            for card in self.cards:
                if card.is_listening:
                    assigned = card.assign_keybind_from_event(name)
                    if assigned:
                        return
            now = time.time()
            last = self._last_trigger_times.get(name, 0)
            if now - last < self._min_trigger_interval:
                return
            self._last_trigger_times[name] = now
            # trigger only if game window is Sonoyuncu
            for card in self.cards:
                if card.enabled and card.keybind and not card.is_listening:
                    if card.keybind == name and card.in_game():
                        card.start_execute_thread()
                        break

        def on_mouse_click(x, y, button, pressed):
            if not self._running or not pressed:
                return
            name = _MOUSE_BUTTON_TO_NAME.get(button)
            if not name:
                return
            # record last physical mouse button
            if not self.is_suppressed():
                self._last_physical_key_name = name
                self._last_physical_key_time = time.time()
            if self.is_suppressed():
                return
            # assignment mode
            for card in self.cards:
                if card.is_listening:
                    assigned = card.assign_keybind_from_event(name)
                    if assigned:
                        return
            now = time.time()
            last = self._last_trigger_times.get(name, 0)
            if now - last < self._min_trigger_interval:
                return
            self._last_trigger_times[name] = now
            for card in self.cards:
                if card.enabled and card.keybind and not card.is_listening:
                    if card.keybind == name and card.in_game():
                        card.start_execute_thread()
                        break

        self.k_listener = pk.Listener(on_press=on_key_press)
        self.m_listener = pm.Listener(on_click=on_mouse_click)
        self.k_listener.start()
        self.m_listener.start()

    def on_close(self):
        self._running = False
        try:
            if self.k_listener:
                self.k_listener.stop()
            if self.m_listener:
                self.m_listener.stop()
        except Exception:
            pass
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            self.window.destroy()
        except Exception:
            pass

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = KyrixClient()
    app.run()