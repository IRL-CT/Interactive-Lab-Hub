# show_on_vnc.py
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk
import time

W, H = 240, 135
img = Image.new("RGB", (W, H), (0, 0, 0))
draw = ImageDraw.Draw(img)

root = tk.Tk()
root.title("Painter Test")

canvas = tk.Canvas(root, width=W*3, height=H*3, bg="black", highlightthickness=0)
canvas.pack()

tk_img = None

def update_canvas():
    global tk_img
    # Draw something simple that changes over time
    draw.rectangle((0, 0, W, H), fill="black")
    draw.ellipse((30, 30, 90, 90), fill=(255, 100, int(time.time()*50) % 255))
    tk_img = ImageTk.PhotoImage(img.resize((W*3, H*3)))
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    root.after(100, update_canvas)  # update every 100 ms

update_canvas()
root.mainloop()
