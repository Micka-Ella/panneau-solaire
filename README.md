# Panneau Solaire - Simulation simple (Tkinter + SQL Server)

Application desktop Python pour:
- creer une simulation,
- ajouter les entrees (materiel, puissance, tranche, duree),
- afficher le resultat de dimensionnement.

Le resultat n'est pas stocke en base. Seules les entrees sont stockees.

---

## Prerequis

- Docker
- Python 3.10+
- ODBC Driver SQL Server (17 ou 18)
- pyodbc (via requirements.txt)

---

## 1. SQL Server avec Docker

```bash
docker pull mcr.microsoft.com/mssql/server:2022-latest

docker run -e "ACCEPT_EULA=Y" `
  -e "MSSQL_SA_PASSWORD=admin@12345" `
  -p 1433:1433 `
  --name sqlserver-solaire `
  -d mcr.microsoft.com/mssql/server:2022-latest
```

---

## 2. Creer manuellement la base et les tables

1. Creer la base `solaire_db` dans SQL Server.
2. Executer le script de creation des tables:

- [database/table_sqlserver.sql](database/table_sqlserver.sql)

3. Executer le script des donnees initiales:

- [database/data.sql](database/data.sql)

Exemple avec sqlcmd:

<!-- ```bash
docker exec -it sqlserver-solaire /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "admin@12345" -C -Q "IF DB_ID('solaire_db') IS NULL CREATE DATABASE solaire_db;"
docker cp database/table_sqlserver.sql sqlserver-solaire:/tmp/table_sqlserver.sql
docker exec -it sqlserver-solaire /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "admin@12345" -C -d solaire_db -i /tmp/table_sqlserver.sql
docker cp database/data.sql sqlserver-solaire:/tmp/data.sql
docker exec -it sqlserver-solaire /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "admin@12345" -C -d solaire_db -i /tmp/data.sql
``` -->

# ✅ Vérifier qu’il tourne
```bash
docker ps
```
- Tu dois voir sqlserver-solaire

# ✅ Créer la base
```bash
docker exec -it sqlserver-solaire /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "admin@12345" -C -Q "IF DB_ID('solaire_db') IS NULL CREATE DATABASE solaire_db;"
```

# ✅ Copier les fichiers SQL
```bash
docker cp .\database\table_sqlserver.sql sqlserver-solaire:/tmp/table_sqlserver.sql
docker cp .\database\data.sql sqlserver-solaire:/tmp/data.sql
```

# ✅ Exécuter scripts SQL
```bash
docker exec -it sqlserver-solaire /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "admin@12345" -C -d solaire_db -i /tmp/table_sqlserver.sql

docker exec -it sqlserver-solaire /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "admin@12345" -C -d solaire_db -i /tmp/data.sql
```



---

## 3. Installer Python

```bash
python -m venv .venv
.\.venv\Scripts\Activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Lancer l'application

```bash
.\.venv\Scripts\python.exe .\src\app_tkinter.py
```

Aucune page de connexion n'est affichee dans l'UI.
La connexion DB se fait en interne avec ces variables d'environnement (optionnel):

- `DB_SERVER` (defaut: `localhost`)
- `DB_PORT` (defaut: `1433`)
- `DB_NAME` (defaut: `solaire_db`)
- `DB_USER` (defaut: `sa`)
- `DB_PASSWORD` (defaut: `admin@12345`)
- `DB_DRIVER` (optionnel)

---

## 5. Flux dans l'application

1. Creer une simulation.
2. Selectionner la simulation active.
3. Ajouter des entrees:
   - materiel,
   - puissance (W),
   - tranche (`MATIN` / `SOIR` / `NUIT`),
   - duree (h).
4. Cliquer sur `Calculer` pour voir le resultat.

---

## Regles de calcul appliquees

- Matin: panneau seul.
- Soir: panneau seul avec 50% disponible.
- Nuit: batterie seule.
- Panneau pratique a acheter: theorique / 0.4.
- Batterie pratique a acheter: batterie_theorique * 1.5.

Aucune alerte "insuffisance" n'est affichee.
