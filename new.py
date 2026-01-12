import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tkinter import Tk, Label, Entry, Button, filedialog, Text, Frame
from matplotlib.backends.backend_pdf import PdfPages
import os

# ============================
# LOGICA CALCOLI ROBUSTA
# ============================

def get_eur(sj_csv, cmj_csv):
    try:
        df_sj = pd.read_csv(sj_csv)
        df_cmj = pd.read_csv(cmj_csv)
        h_sj = float(df_sj[df_sj.iloc[:, 0].str.contains('Altezza', na=False)].iloc[0, 1])
        h_cmj = float(df_cmj[df_cmj.iloc[:, 0].str.contains('Altezza', na=False)].iloc[0, 1])
        return h_sj, h_cmj, h_cmj / h_sj
    except Exception as e:
        print(f"Errore lettura EUR: {e}")
        return None

def calculate_stiffness_metrics(file_path, massa, soglia=20):
    try:
        df = pd.read_csv(file_path, sep=",", header=None, comment="#").iloc[:, :3]
        df.columns = ["time", "sx", "dx"]
        
        # Calcolo automatico OFFSET basato sui primi campioni del file
        offset_sx = df['sx'].iloc[:20].mean()
        offset_dx = df['dx'].iloc[:20].mean()
        
        df['sx_cor'] = (df['sx'] - offset_sx).clip(lower=0)
        df['dx_cor'] = (df['dx'] - offset_dx).clip(lower=0)
        df['forza'] = (df['sx_cor'] + df['dx_cor']).rolling(5).mean()
        df['time_s'] = df['time'] / 1000
        
        is_contact = df['forza'] > soglia
        diff = is_contact.astype(int).diff().fillna(0)
        
        starts = df.loc[diff == 1, 'time_s'].values
        ends = df.loc[diff == -1, 'time_s'].values
        
        if len(starts) < 3: return None
        if ends[0] < starts[0]: ends = ends[1:]
        n = min(len(starts), len(ends))
        
        tc = np.mean(ends[:n] - starts[:n])
        tv = np.mean(starts[1:n] - ends[:n-1])
        rsi = tv / tc
        k_vert = (massa * np.pi * tv) / (tc**2 * (tv + tc))
        
        return tc, tv, rsi, k_vert
    except Exception as e:
        print(f"Errore Stiffness: {e}")
    return None

# ============================
# INTERFACCIA E EXPORT PDF + CSV
# ============================

class PerformanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Report Magistrale: EUR & Stiffness")
        
        Label(root, text="Massa Atleta (kg):", font=('Arial', 10, 'bold')).grid(row=0, column=0, pady=10)
        self.massa_entry = Entry(root); self.massa_entry.insert(0, "75")
        self.massa_entry.grid(row=0, column=1)

        Button(root, text="1. CARICA SJ + CMJ (Profilo EUR)", command=self.run_eur, width=40, bg="#e1f5fe").grid(row=1, columnspan=2, pady=5)
        Button(root, text="2. CARICA BALZELLI (Stiffness)", command=self.run_stiffness, width=40, bg="#e8f5e9").grid(row=2, columnspan=2, pady=5)
        Button(root, text="3. GENERA REPORT FINALE (PDF + CSV)", command=self.export_final, width=40, bg="#ffcc80", font=('Arial', 10, 'bold')).grid(row=3, columnspan=2, pady=20)

        self.txt = Text(root, height=10, width=60, font=('Consolas', 9))
        self.txt.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        self.results = {}

    def run_eur(self):
        f_sj = filedialog.askopenfilename(title="Seleziona CSV Squat Jump")
        f_cmj = filedialog.askopenfilename(title="Seleziona CSV CMJ")
        if f_sj and f_cmj:
            res = get_eur(f_sj, f_cmj)
            if res:
                h_sj, h_cmj, eur = res
                self.results['eur'] = {'sj': h_sj, 'cmj': h_cmj, 'eur': eur}
                self.txt.insert("end", f"> EUR CALCOLATO: {eur:.2f}\n")

    def run_stiffness(self):
        f_b = filedialog.askopenfilename(title="Seleziona File Balzelli")
        try:
            m = float(self.massa_entry.get())
            if f_b:
                m_stiff = calculate_stiffness_metrics(f_b, m)
                if m_stiff:
                    tc, tv, rsi, kv = m_stiff
                    self.results['stiff'] = {'tc': tc, 'tv': tv, 'rsi': rsi, 'kv': kv}
                    self.txt.insert("end", f"> STIFFNESS: RSI {rsi:.2f} | K {kv/1000:.1f} kN/m\n")
        except: self.txt.insert("end", "[ERRORE] Massa non valida\n")

    def export_final(self):
        if not self.results: return
        
        path_base = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Report_Performance.pdf")
        if not path_base: return
        
        # --- PREPARAZIONE DATI PER CSV (struttura compatibile con compare.py) ---
        csv_data = []
        if 'eur' in self.results:
            csv_data.append(["Altezza SJ (cm)", f"{self.results['eur']['sj']:.1f}"])
            csv_data.append(["Altezza CMJ (cm)", f"{self.results['eur']['cmj']:.1f}"])
            csv_data.append(["EUR (Efficienza)", f"{self.results['eur']['eur']:.2f}"])
        if 'stiff' in self.results:
            csv_data.append(["RSI (Reattivita)", f"{self.results['stiff']['rsi']:.2f}"])
            csv_data.append(["Vertical Stiffness (kN/m)", f"{self.results['stiff']['kv']/1000:.2f}"])
            csv_data.append(["T. Contatto (s)", f"{self.results['stiff']['tc']:.3f}"])
        
        # --- EXPORT CSV ---
        csv_path = path_base.replace(".pdf", ".csv")
        df_csv = pd.DataFrame(csv_data, columns=["Parametro", "Valore"])
        df_csv.to_csv(csv_path, index=False)

        # --- EXPORT PDF ---
        with PdfPages(path_base) as pdf:
            fig, ax = plt.subplots(figsize=(8.5, 11))
            ax.axis('off')
            table = ax.table(cellText=csv_data, colLabels=["Parametro", "Valore"], loc='center', cellLoc='left')
            table.set_fontsize(12); table.scale(1.2, 2.5)
            plt.title("VALUTAZIONE NEUROMUSCOLARE", fontsize=16, fontweight='bold', pad=30)
            pdf.savefig(); plt.close()
        
        self.txt.insert("end", f"\n*** EXPORT COMPLETATO ***\nPDF: {os.path.basename(path_base)}\nCSV: {os.path.basename(csv_path)}\n")

if __name__ == "__main__":
    root = Tk(); app = PerformanceApp(root); root.mainloop()