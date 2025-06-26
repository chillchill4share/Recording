import tkinter as tk

class ToolTip:
    """
    Lớp tạo tooltip (hướng dẫn khi di chuột) cho các widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.toplevel = self.widget.winfo_toplevel()
        self.toplevel.bind("<Configure>", self.update_tip_position, add="+")
        self.widget.bind("<Configure>", self.update_tip_position, add="+")

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)
        self.update_tip_position()

    def update_tip_position(self, event=None):
        if not self.tip_window or not self.tip_window.winfo_exists():
            return
        
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Đảm bảo tooltip không bị che khuất ở dưới màn hình
        if y + self.tip_window.winfo_height() > self.toplevel.winfo_screenheight():
             y = self.widget.winfo_rooty() - self.tip_window.winfo_height() - 5
             
        self.tip_window.wm_geometry(f"+{x}+{y}")

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None

def center_dialog(dialog):
    """Đặt vị trí dialog chính giữa cửa sổ cha."""
    if not dialog.winfo_exists():
        return
    dialog.update_idletasks()
    parent = dialog.master
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    x = parent_x + (parent_width - dialog_width) // 2
    y = parent_y + (parent_height - dialog_height) // 2
    dialog.geometry(f"+{x}+{y}")