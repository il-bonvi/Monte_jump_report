import pandas as pd
import tkinter as tk
from tkinter import filedialog, Label, Button, Text, Frame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# ============================
# VARIABILI GLOBALI
# ============================
pre_file = None
post_file = None
pre_data = None
post_data = None

# ============================
# FUNZIONI
# ============================

def load_csv(pre_or_post):
    global pre_file, post_file, pre_data, post_data
    file_path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not file_path:
        return
    if pre_or_post == "pre":
        pre_file = file_path
        pre_data = pd.read_csv(file_path)
        pre_label.config(text=f"Pre: {os.path.basename(file_path)}")
    else:
        post_file = file_path
        post_data = pd.read_csv(file_path)
        post_label.config(text=f"Post: {os.path.basename(file_path)}")
    update_preview()

def update_preview():
    preview_text.delete("1.0", "end")
    if pre_data is None or post_data is None:
        return

    # Allinea i parametri (assumiamo che siano identici)
    combined = pd.DataFrame({
        "Parametro": pre_data['Parametro'],
        "Pre": pre_data['Valore'],
        "Post": post_data['Valore']
    })
    preview_text.insert("end", combined.to_string(index=False))
    update_plot(combined)

def update_plot(df):
    for widget in plot_frame.winfo_children():
        widget.destroy()
    # Grafico a barre confronto
    fig, ax = plt.subplots(figsize=(8,5))
    param = df['Parametro']
    pre_vals = pd.to_numeric(df['Pre'], errors='coerce')
    post_vals = pd.to_numeric(df['Post'], errors='coerce')
    x = range(len(param))
    width = 0.35
    ax.bar(x, pre_vals, width=width, label='Pre', color='skyblue')
    ax.bar([i + width for i in x], post_vals, width=width, label='Post', color='orange')
    ax.set_xticks([i + width/2 for i in x])
    ax.set_xticklabels(param, rotation=45, ha='right')
    ax.set_ylabel('Valore')
    ax.set_title('Confronto Pre vs Post')
    ax.legend()
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack()

# ============================
# GUI
# ============================

root = tk.Tk()
root.title("Confronto Pre/Post CMJ")

Button(root, text="Seleziona CSV Pre", command=lambda: load_csv("pre")).grid(row=0, column=0, pady=5)
pre_label = Label(root, text="Pre: nessun file selezionato")
pre_label.grid(row=0, column=1, sticky='w')

Button(root, text="Seleziona CSV Post", command=lambda: load_csv("post")).grid(row=1, column=0, pady=5)
post_label = Label(root, text="Post: nessun file selezionato")
post_label.grid(row=1, column=1, sticky='w')

preview_text = Text(root, height=15, width=70)
preview_text.grid(row=2, column=0, columnspan=2, pady=5)

plot_frame = Frame(root)
plot_frame.grid(row=3, column=0, columnspan=2, pady=5)

root.mainloop()
