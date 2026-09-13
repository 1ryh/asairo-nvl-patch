"""Windows GUI entry point; bundled with Python and Tk in release builds."""
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from installer import core


class Installer:
    def __init__(self, root):
        self.root = root
        self.busy = False
        self.events = queue.Queue()
        root.title('Asairo Native NVL — Installer')
        root.geometry('660x450')
        root.minsize(620, 430)
        root.protocol('WM_DELETE_WINDOW', self.close)
        frame = ttk.Frame(root, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Asairo Native NVL', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(frame, text='Install or remove the native reading-window patch.', wraplength=590).pack(anchor='w', pady=(4, 18))
        ttk.Label(frame, text='First, copy your working game to a separate folder ending in (Copy),\nfor example: C:\\Games\\Asairo (Copy). Close the game before continuing.', wraplength=590).pack(anchor='w')
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=14)
        self.folder = tk.StringVar()
        self.entry = ttk.Entry(row, textvariable=self.folder)
        self.entry.pack(side='left', fill='x', expand=True)
        self.browse = ttk.Button(row, text='Choose folder…', command=self.choose)
        self.browse.pack(side='left', padx=(8, 0))
        actions = ttk.Frame(frame)
        actions.pack(fill='x')
        self.buttons = []
        for title, action in [('Install / Repair', 'install'), ('Check', 'check'), ('Remove patch', 'remove')]:
            button = ttk.Button(actions, text=title, command=lambda a=action: self.start(a))
            button.pack(side='left', padx=(0, 8))
            self.buttons.append(button)
        self.message = tk.StringVar(value='Choose the folder containing asairo.exe.')
        ttk.Label(frame, textvariable=self.message, wraplength=590, justify='left').pack(anchor='w', pady=18)
        self.progress = ttk.Progressbar(frame, mode='indeterminate')
        self.progress.pack(fill='x')
        ttk.Label(frame, text='Experimental: native Windows gameplay is not yet validated.\nYour executable and game archives stay unchanged. Changes and saves are backed up.\nLoad NVL saves with the patch enabled.', wraplength=590, foreground='#555555').pack(anchor='w', pady=(18, 0))
        root.after(100, self.poll)

    def choose(self):
        folder = filedialog.askdirectory(title='Choose your separate game (Copy) folder', mustexist=True)
        if folder:
            self.folder.set(folder)

    def start(self, action):
        if self.busy:
            return
        folder = self.folder.get().strip()
        if not folder:
            messagebox.showinfo('Choose a game folder', 'Select the folder containing asairo.exe first.')
            return
        if action == 'remove' and not messagebox.askokcancel('Remove NVL patch', 'After removal, use a pre-NVL save or start a new game. NVL saves need this patch enabled.\n\nRemove the patch?'):
            return
        self.busy = True
        for widget in [self.entry, self.browse, *self.buttons]:
            widget.configure(state='disabled')
        self.message.set('Checking game files…')
        self.progress.start()
        threading.Thread(target=self.work, args=(folder, action), daemon=True).start()

    def work(self, folder, action):
        try:
            if action == 'check':
                state = core.status(folder)
                result = {'NVL': 'NVL is installed. Launch asairo.exe from this folder.',
                          'ADV': 'The patch is not installed. Select Install / Repair to enable NVL.',
                          'INCOMPLETE': 'Some patch files are missing. Select Install / Repair or Remove patch.'}[state]
            else:
                result = core.change(folder, action == 'install', lambda text: self.events.put(('progress', text)))
                if action == 'install':
                    result += '\nLaunch asairo.exe from the selected folder to play.'
            self.events.put(('done', result))
        except Exception as error:
            self.events.put(('error', str(error) or type(error).__name__))

    def poll(self):
        try:
            while True:
                kind, text = self.events.get_nowait()
                self.message.set(text)
                if kind != 'progress':
                    self.busy = False
                    self.progress.stop()
                    for widget in [self.entry, self.browse, *self.buttons]:
                        widget.configure(state='normal')
                    if kind == 'error':
                        messagebox.showerror('Could not complete the operation', text)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('Operation in progress', 'Please wait for the current operation to finish before closing.')
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    Installer(root)
    if '--self-test' in sys.argv:
        # Used by the Windows build to exercise bundled Tk, imports and payload data.
        import hashlib
        from tools.panel import rounded_panel
        rows = core.manifest()
        assert core.digest(core.ROOT / 'patch-files/winmm.dll') == next(r['sha256'] for r in rows if r['path'] == 'winmm.dll')
        assert hashlib.sha256(rounded_panel()).hexdigest() == next(r['sha256'] for r in rows if r['path'] == 'BG/NV00.mgr')
        core.require_closed()
        root.update()
        root.destroy()
        return
    root.mainloop()


if __name__ == '__main__':
    main()
