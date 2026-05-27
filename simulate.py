import argparse
import concurrent.futures
import os
import time

import nbformat
from nbclient import NotebookClient

from monitor import ResourceMonitor

# Durée (secondes) de stabilisation entre deux paliers d'utilisateurs
PAUSE_ENTRE_PALIERS = 60


def executer_notebook(notebook_path: str, user_id: int) -> tuple[int, int, float]:
    """Exécute le notebook et retourne (user_id, code_retour, durée_s)."""
    debut = time.time()
    try:
        nb = nbformat.read(notebook_path, as_version=4)
        client = NotebookClient(nb, timeout=900, kernel_name="python3")
        client.execute()
        return user_id, 0, round(time.time() - debut, 1)
    except Exception:
        return user_id, 1, round(time.time() - debut, 1)


def simuler_palier(notebook_path: str, gabarit: str, nb_users: int, output_csv: str):
    print(f"\n{'='*60}")
    print(f"  Gabarit : {gabarit}  |  Utilisateurs : {nb_users}")
    print(f"{'='*60}")

    monitor = ResourceMonitor(output_csv, gabarit, nb_users, interval=1.0)
    monitor.start()
    t_debut = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=nb_users) as executor:
        futures  = [executor.submit(executer_notebook, notebook_path, i) for i in range(nb_users)]
        resultats = [f.result() for f in concurrent.futures.as_completed(futures)]

    duree_totale = round(time.time() - t_debut, 1)
    monitor.stop()

    print(f"\n  Résultats individuels :")
    for user_id, code, duree in sorted(resultats):
        statut = "OK" if code == 0 else f"ERREUR (code {code})"
        print(f"    Utilisateur {user_id:>2} : {statut} — {duree}s")
    print(f"\n  Durée totale du palier : {duree_totale}s")

    nb_ok     = sum(1 for _, code, _ in resultats if code == 0)
    nb_erreur = nb_users - nb_ok
    if nb_erreur:
        print(f"  /!\\ {nb_erreur} notebook(s) en erreur sur {nb_users}")


def main():
    parser = argparse.ArgumentParser(description="Simulation de charge JupyterHub")
    parser.add_argument("--notebook", required=True,  help="Chemin vers le notebook de référence")
    parser.add_argument("--gabarit",  required=True,  help="Nom du gabarit VM (ex : medium, large)")
    parser.add_argument("--users",    nargs="+", type=int, default=[1, 2, 5, 10, 20],
                        help="Liste du nombre d'utilisateurs à simuler")
    parser.add_argument("--output",   default="resultats/resultats.csv", help="Fichier CSV de sortie")
    parser.add_argument("--pause",    type=int, default=PAUSE_ENTRE_PALIERS,
                        help="Secondes de pause entre deux paliers (stabilisation)")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    for i, n in enumerate(args.users):
        simuler_palier(args.notebook, args.gabarit, n, args.output)
        if i < len(args.users) - 1:
            print(f"\n  Pause de {args.pause}s avant le palier suivant…")
            time.sleep(args.pause)

    print(f"\nTest terminé. Résultats dans : {args.output}")


if __name__ == "__main__":
    main()