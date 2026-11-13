# Frigate Kerherve

Complément de l'intégration Frigate officielle pour Home Assistant (elle reste installée, rien n'est remplacé).

## Ce que ça ajoute
- **Santé par caméra** : qualité de connexion, reconnexions et blocages sur 1 h, charge ffmpeg, images par seconde, et un capteur « Problème ».
- **Santé du serveur** : charge, mémoire, disque des enregistrements, vitesses (détection, visages, plaques, descriptions IA), durée de marche.
- **Services** : `frigate_kerherve.set_config`, `get_config`, `restart`, `list_faces`, `delete_faces`, `classify_face`.

Lecture de `/api/stats` une fois par minute. Aucune IA, aucun cloud.

## Installation
1. HACS → dépôts personnalisés → `https://github.com/mkerhervemk-png/ha-frigate-kerherve` (type Intégration) → Télécharger.
2. Redémarrer Home Assistant.
3. Paramètres → Appareils et services → Ajouter → « Frigate Kerherve ». Adresse par défaut : `http://ccab4aaf-frigate-fa:5000`.

## Limites
- `delete_faces` et `classify_face` n'ont pas été testés en réel dans la version 0.1.0.
- Le capteur « Problème » s'active à 0 image/s, 5 reconnexions ou 20 blocages sur 1 h (seuils dans `const.py`).
