
### Contenu du dépôt :

- `CODE` : Code source du projet 
- `DOCS` : Documentation du projet et des éxécutions du code

### Guide d'installation

1. Installer Anaconda ou Miniconda
[Installer Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install)

2. Installer ShapeWorks
[Installer ShapeWorks](https://sciinstitute.github.io/ShapeWorks/latest/users/install.html)

**Note :** Le programme fonctionne correctement sur Windows
La compatibilité n'a pas été testée sur Linux ou MacOS

3. Installer les dépendances manquantes

Lors de l'étape 1, l'environnement `shapeworks` est créé. 
Pour installer les dépendances manquantes, lancer la commande suivante :
```bash
conda activate shapeworks
conda install -r requirements.txt
```

**Note :** Si l'environnement présente des problèmes de compatibilité, re-créez l'environnemnt shapeworks depuis zéro (de la même manière que l'étape 1) et installez manuellement les dépendances manquantes.

### Éxécution du programme

- Lancer le projet depuis le root folder (celui ci)
- Avant d'ouvrir le fichier `swproj` généré, fermez tous les autres programmes pour éviter des crash
