# 📘 API Flask avec Neo4j
Ce projet est une API RESTful développée avec Flask et Neo4j (via Docker), permettant de gérer des utilisateurs, leurs relations, des posts, des commentaires, et des likes.

## 🚀 Objectifs
Créer une API RESTful avec Flask.

Gérer des données liées sous forme de graphe via Neo4j.

Implémenter les entités : Utilisateurs, Posts, Commentaires.

Gérer les relations entre entités (amis, likes, etc).

## 🛠️ Prérequis
Python 3.8+

Docker

Neo4j (via Docker recommandé)

Postman pour tester les routes

## 🧱 Installation
1. Cloner le projet
   ``` git clone <[URL_DU_REPO](https://github.com/CorentinLartigue/Tp_Neo4J.git)> ```
   ``` cd <Tp_Neo4J> ```

2. Installer les dépendances Python
   ``` pip install flask py2neo ```

3. Lancer Neo4j avec Docker
  ``` docker run --name neo4j -d \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j
```

4. Lancer l'application Flask
  Run via le terminal

### Accès API : http://localhost:5000
### Accès interface Neo4j : http://localhost:7474

## Tester les routes :

Importer dans postman le fichier json CRUD Neo4J Postman
