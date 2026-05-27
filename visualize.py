
import argparse
import os

import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import pandas as pd

METRICS = {
    "cpu_percent":      ("Utilisation CPU",       "%",  (0, 100)),
    "ram_percent":      ("Utilisation RAM",        "%",  (0, 100)),
    "gpu_util_percent": ("Charge GPU",             "%",  (0, 100)),
    "gpu_mem_used_mb":  ("Mémoire GPU utilisée",   "Mo", None),
    "gpu_temp_c":       ("Température GPU",        "°C", (0, 100)),
}


def charger_donnees(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values(["gabarit", "nb_users", "timestamp"])
    return df


# ── Figure 1 : Évolution temporelle par nombre d'utilisateurs ────────────────

def plot_evolution_temporelle(df: pd.DataFrame, gabarit: str, metrique: str, out_dir: str):
    label, unite, ylim = METRICS[metrique]
    sous = df[df["gabarit"] == gabarit]
    paliers = sorted(sous["nb_users"].unique())

    fig, ax = plt.subplots(figsize=(12, 5))
    couleurs = cm.viridis(np.linspace(0, 0.9, len(paliers)))

    for couleur, n in zip(couleurs, paliers):
        segment = sous[sous["nb_users"] == n].copy()
        # Normaliser le temps à t=0 pour chaque palier
        segment["t"] = (segment["timestamp"] - segment["timestamp"].min()).dt.total_seconds()
        ax.plot(segment["t"], segment[metrique], color=couleur, label=f"{n} utilisateur(s)", linewidth=1.2)

    ax.set_title(f"{label} — gabarit {gabarit}")
    ax.set_xlabel("Temps (s)")
    ax.set_ylabel(f"{label} ({unite})")
    if ylim:
        ax.set_ylim(ylim)
    ax.legend(title="Utilisateurs simultanés", bbox_to_anchor=(1.01, 1), loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    nom = f"{out_dir}/{gabarit}_{metrique}_evolution.png"
    fig.savefig(nom, dpi=150)
    plt.close(fig)
    print(f"  Sauvegardé : {nom}")


# ── Figure 2 : Pic de ressource par palier (bar chart) ──────────────────────

def plot_pics_par_palier(df: pd.DataFrame, gabarit: str, metrique: str, out_dir: str):
    label, unite, ylim = METRICS[metrique]
    sous   = df[df["gabarit"] == gabarit]
    pics   = sous.groupby("nb_users")[metrique].max().reset_index()

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(pics["nb_users"].astype(str), pics[metrique], color="#1a3a5c", edgecolor="white")
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=9)

    ax.set_title(f"Pic de {label.lower()} — gabarit {gabarit}")
    ax.set_xlabel("Nombre d'utilisateurs simultanés")
    ax.set_ylabel(f"{label} ({unite})")
    if ylim:
        ax.set_ylim(0, ylim[1] * 1.1)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()

    nom = f"{out_dir}/{gabarit}_{metrique}_pics.png"
    fig.savefig(nom, dpi=150)
    plt.close(fig)
    print(f"  Sauvegardé : {nom}")


# ── Figure 3 : Heatmap gabarit × nb_users ───────────────────────────────────

def plot_heatmap(df: pd.DataFrame, metrique: str, out_dir: str):
    label, unite, _ = METRICS[metrique]
    pivot = df.groupby(["gabarit", "nb_users"])[metrique].max().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(max(6, len(pivot.columns)), max(4, len(pivot))))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    plt.colorbar(im, ax=ax, label=f"{label} ({unite})")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    ax.set_xlabel("Nombre d'utilisateurs")
    ax.set_ylabel("Gabarit VM")
    ax.set_title(f"Heatmap — Pic de {label.lower()} par gabarit et charge")

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            ax.text(j, i, f"{pivot.values[i, j]:.0f}", ha="center", va="center", fontsize=8)

    fig.tight_layout()
    nom = f"{out_dir}/heatmap_{metrique}.png"
    fig.savefig(nom, dpi=150)
    plt.close(fig)
    print(f"  Sauvegardé : {nom}")


# ── Figure 4 : Comparaison multi-gabarits pour une métrique ─────────────────

def plot_comparaison_gabarits(df: pd.DataFrame, metrique: str, out_dir: str):
    label, unite, ylim = METRICS[metrique]
    gabarits = df["gabarit"].unique()
    couleurs = cm.tab10(np.linspace(0, 1, len(gabarits)))

    fig, ax = plt.subplots(figsize=(10, 5))
    for couleur, g in zip(couleurs, gabarits):
        pics = df[df["gabarit"] == g].groupby("nb_users")[metrique].max().reset_index()
        ax.plot(pics["nb_users"], pics[metrique], marker="o", color=couleur, label=g, linewidth=1.8)

    ax.set_title(f"Pic de {label.lower()} — comparaison des gabarits")
    ax.set_xlabel("Nombre d'utilisateurs simultanés")
    ax.set_ylabel(f"{label} ({unite})")
    if ylim:
        ax.set_ylim(0, ylim[1] * 1.05)
    ax.legend(title="Gabarit VM")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    nom = f"{out_dir}/comparaison_gabarits_{metrique}.png"
    fig.savefig(nom, dpi=150)
    plt.close(fig)
    print(f"  Sauvegardé : {nom}")


# ── Entrée principale ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Visualisation des résultats de charge JupyterHub")
    parser.add_argument("--input",  default="resultats/resultats.csv",  help="Fichier CSV de résultats")
    parser.add_argument("--output", default="resultats/figures/",       help="Répertoire de sortie des figures")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    df = charger_donnees(args.input)

    print(f"\nDonnées chargées : {len(df)} mesures")
    print(f"  Gabarits  : {sorted(df['gabarit'].unique())}")
    print(f"  Paliers   : {sorted(df['nb_users'].unique())}\n")

    for gabarit in df["gabarit"].unique():
        print(f"[{gabarit}] Génération des graphiques…")
        for metrique in METRICS:
            plot_evolution_temporelle(df, gabarit, metrique, args.output)
            plot_pics_par_palier(df, gabarit, metrique, args.output)

    for metrique in METRICS:
        plot_heatmap(df, metrique, args.output)
        plot_comparaison_gabarits(df, metrique, args.output)

    print("\nVisualisation terminée.")


if __name__ == "__main__":
    main()