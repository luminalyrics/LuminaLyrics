# 🎶 LuminaLyrics

LuminaLyrics est une application web moderne permettant de générer automatiquement des "Lyrics Videos" (vidéos de paroles) et des visualiseurs audio à partir de votre musique, d'images et d'un fichier de paroles synchronisées (LRC/SRT).

Le projet se compose d'une interface frontend réactive en Angular et d'un backend puissant en Python utilisant FFmpeg pour le montage vidéo.

---

## 🌟 Fonctionnalités

- **Génération automatique** de vidéos musicales avec paroles synchronisées.
- **Visualiseur Audio réactif** : Les effets visuels réagissent au BPM (tempo) de la musique.
- **Upload multi-fichiers** : Accepte des audios (.mp3, .wav), des paroles (.lrc, .srt), des images d'arrière-plan et des polices personnalisées (.ttf).
- **Interface UI premium** : Design sombre, moderne avec un workflow intuitif développé sous Angular.
- **Traitement asynchrone** : Le backend gère les rendus vidéo en arrière-plan sans bloquer l'interface.

---

## 🛠️ Stack Technique

### Frontend
- **Framework :** Angular (Standalone Components)
- **Styling :** CSS Vanilla, Google Fonts (Inter)
- **Intégration Ads :** Prêt pour Google AdSense

### Backend
- **Framework API :** FastAPI, Python 3
- **Traitement Média :** FFmpeg, Librosa (pour la détection de BPM)
- **Montage Vidéo :** MoviePy

---

## 🚀 Installation & Démarrage local

### 1. Prérequis
- **Node.js** (v18 ou supérieur) et **npm**
- **Python** (v3.9 ou supérieur)
- **FFmpeg** installé sur votre machine et ajouté au PATH (indispensable pour la génération vidéo).

### 2. Configuration du Backend (Python)

Ouvrez un terminal et placez-vous dans le dossier `backend` :

```bash
cd backend

# Création de l'environnement virtuel
python -m venv venv

# Activation de l'environnement (Windows)
.\venv\Scripts\activate
# ou (Mac/Linux) : source venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Démarrage du serveur FastAPI
python main.py
```
L'API tournera sur `http://127.0.0.1:8000`.

### 3. Configuration du Frontend (Angular)

Ouvrez un nouveau terminal et placez-vous dans le dossier `frontend` :

```bash
cd frontend

# Installation des packages
npm install

# Lancement du serveur de développement
npm start
```
Le frontend sera accessible sur `http://localhost:4200`.

---

## 📂 Structure du projet

```
LuminaLyrics/
├── backend/                  # Serveur Python & logique de rendu vidéo
│   ├── main.py               # API FastAPI et gestion des tâches asynchrones
│   ├── video_generator.py    # Algorithmes MoviePy (rendu des textes, effets)
│   ├── audio_analyzer.py     # Analyse Librosa (BPM, tempo)
│   └── lyrics_parser.py      # Parseur de fichiers LRC et SRT
├── frontend/                 # Interface Angular
│   └── src/app/              # Composants (Home, Generator, AdBanner)
└── .gitignore                # Fichier d'exclusion (venv, node_modules, etc.)
```

---

## 📜 Licence

Projet privé. Développé par LuminaLyrics.
