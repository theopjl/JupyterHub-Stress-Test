# Stress test JupyterHub

Outil de simulation de charge pour JupyterHub. Le principe est d'exécuter un notebook de référence en parallèle pour un nombre croissant d'utilisateurs simultanés (paliers), tout en enregistrant en continu les ressources système (CPU, RAM, GPU). Les résultats sont ensuite visualisés sous forme de graphiques.

## Structure

```
jhub-test/
├── simulate.py           # Simulation de charge (script principal)
├── monitor.py            # Moniteur de ressources (CPU/RAM/GPU → CSV)
├── visualize.py          # Génération des graphiques à partir du CSV
├── mnist_reference.ipynb # Notebook de référence exécuté par les utilisateurs simulés
├── data/                 # Données MNIST
└── resultats/
    ├── resultats.csv     # Mesures de ressources produites par simulate.py
    └── figures/          # Graphiques produits par visualize.py
```

## Dépendances

```bash
pip install nbformat nbclient psutil matplotlib pandas numpy torch torchvision
```

> `nvidia-smi` doit être disponible sur la machine pour que les métriques GPU soient collectées. Sans GPU, les colonnes GPU sont remplies à 0.

---

## 1. Lancer la simulation

```bash
python simulate.py \
    --notebook mnist_reference.ipynb \
    --gabarit  medium \
    --users    1 2 5 10 20 \
    --output   resultats/resultats.csv \
    --pause    60
```

### Paramètres de `simulate.py`

| Paramètre | Obligatoire | Défaut | Description |
|---|---|---|---|
| `--notebook` | Oui | — | Chemin vers le notebook de référence à exécuter. Chaque utilisateur simulé en exécute une copie indépendante. |
| `--gabarit` | Oui | — | Nom libre identifiant le gabarit (profil) de la VM testée (ex. `small`, `medium`, `large`). Ce label est inscrit dans le CSV pour permettre de comparer plusieurs gabarits. |
| `--users` | Non | `1 2 5 10 20` | Liste des paliers de charge : nombre d'utilisateurs simultanés à simuler pour chaque palier. Les paliers sont joués dans l'ordre, séparés par une pause. |
| `--output` | Non | `resultats/resultats.csv` | Chemin du fichier CSV dans lequel les métriques système sont enregistrées. Le répertoire est créé automatiquement si nécessaire. Si le fichier existe déjà, les nouvelles lignes y sont ajoutées (append), ce qui permet d'accumuler les résultats de plusieurs gabarits. |
| `--pause` | Non | `60` | Durée en secondes de la pause de stabilisation entre deux paliers consécutifs. Laisser suffisamment de temps pour que le système revienne à l'état de repos avant le palier suivant. |

### Exemple — tester plusieurs gabarits

Lancez `simulate.py` une fois par gabarit avec le même fichier `--output` pour accumuler toutes les mesures :

```bash
python simulate.py --notebook mnist_reference.ipynb --gabarit small  --users 1 2 5 --output resultats/resultats.csv
python simulate.py --notebook mnist_reference.ipynb --gabarit medium --users 1 2 5 --output resultats/resultats.csv
python simulate.py --notebook mnist_reference.ipynb --gabarit large  --users 1 2 5 --output resultats/resultats.csv
```

---

## 2. Visualiser les résultats

```bash
python visualize.py \
    --input  resultats/resultats.csv \
    --output resultats/figures/
```

### Paramètres de `visualize.py`

| Paramètre | Obligatoire | Défaut | Description |
|---|---|---|---|
| `--input` | Non | `resultats/resultats.csv` | Chemin vers le CSV produit par `simulate.py`. |
| `--output` | Non | `resultats/figures/` | Répertoire de sortie pour les figures PNG. Créé automatiquement si nécessaire. |

### Graphiques générés

Pour chaque gabarit et chaque métrique (`cpu_percent`, `ram_percent`, `gpu_util_percent`, `gpu_mem_used_mb`, `gpu_temp_c`) :

- **`<gabarit>_<métrique>_evolution.png`** — Évolution temporelle de la métrique pendant chaque palier, une courbe par nombre d'utilisateurs.
- **`<gabarit>_<métrique>_pics.png`** — Pic atteint par palier (bar chart).

Pour chaque métrique (toutes gabarits confondus) :

- **`heatmap_<métrique>.png`** — Heatmap gabarit × nombre d'utilisateurs.
- **`comparaison_gabarits_<métrique>.png`** — Pic de la métrique en fonction du nombre d'utilisateurs, une courbe par gabarit.

---

## Format du CSV de résultats

| Colonne | Description |
|---|---|
| `timestamp` | Horodatage ISO 8601 de la mesure |
| `gabarit` | Nom du gabarit fourni à `--gabarit` |
| `nb_users` | Nombre d'utilisateurs simultanés du palier en cours |
| `cpu_percent` | Utilisation CPU globale (%) |
| `ram_used_gb` | RAM consommée (Go) |
| `ram_total_gb` | RAM totale (Go) |
| `ram_percent` | Utilisation RAM (%) |
| `gpu_util_percent` | Charge du GPU (%) |
| `gpu_mem_used_mb` | Mémoire GPU utilisée (Mo) |
| `gpu_mem_total_mb` | Mémoire GPU totale (Mo) |
| `gpu_temp_c` | Température du GPU (°C) |
