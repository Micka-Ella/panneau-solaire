import os

import pyodbc

from modeles import EntreeSimulation, Simulation


class RepositorySqlServer:
    def __init__(self):
        self.serveur = os.getenv("DB_SERVER", "localhost")
        self.port = os.getenv("DB_PORT", "1433")
        self.ports_fallback = os.getenv("DB_PORTS", "1433,11433")
        self.base = os.getenv("DB_NAME", "solaire_db")
        self.utilisateur = os.getenv("DB_USER", "sa")
        self.mot_de_passe = os.getenv("DB_PASSWORD", "admin@12345")
        self.driver_force = os.getenv("DB_DRIVER", "")
        self.cnxn: pyodbc.Connection | None = None

    def _driver_sql_server(self) -> str:
        drivers = pyodbc.drivers()
        if self.driver_force and self.driver_force in drivers:
            return self.driver_force

        for candidat in ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server"]:
            if candidat in drivers:
                return candidat

        for driver in drivers:
            if "SQL Server" in driver:
                return driver

        raise RuntimeError("Aucun driver ODBC SQL Server detecte")

    def _chaine_connexion(self, base: str, port: str) -> str:
        driver = self._driver_sql_server()
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={self.serveur},{port};"
            f"DATABASE={base};"
            f"UID={self.utilisateur};"
            f"PWD={self.mot_de_passe};"
            "Encrypt=no;TrustServerCertificate=yes;"
        )

    def _ports_a_tester(self) -> list[str]:
        candidats: list[str] = []

        if self.port and self.port.strip():
            candidats.append(self.port.strip())

        for p in self.ports_fallback.split(","):
            p = p.strip()
            if p and p not in candidats:
                candidats.append(p)

        return candidats or ["1433"]

    def connecter(self):
        derniere_erreur: Exception | None = None

        for port in self._ports_a_tester():
            try:
                self.cnxn = pyodbc.connect(self._chaine_connexion(self.base, port), timeout=5)
                self.cnxn.autocommit = False
                return
            except Exception as exc:
                derniere_erreur = exc

        if derniere_erreur is not None:
            raise derniere_erreur

    def fermer(self):
        if self.cnxn is not None:
            self.cnxn.close()
            self.cnxn = None

    def _executer(self, sql: str, params=None):
        if self.cnxn is None:
            raise RuntimeError("La connexion SQL Server n'est pas active")
        cur = self.cnxn.cursor()
        cur.execute(sql, params or [])
        return cur

    def lister_simulations(self) -> list[Simulation]:
        cur = self._executer(
            "SELECT id, titre, ISNULL(notes, '') FROM dbo.simulation ORDER BY id DESC"
        )
        return [Simulation(int(r[0]), str(r[1]), str(r[2])) for r in cur.fetchall()]

    def lister_tranches(self) -> list[tuple[int, str]]:
        cur = self._executer("SELECT id, libelle FROM dbo.tranche_heure ORDER BY id")
        return [(int(r[0]), str(r[1])) for r in cur.fetchall()]

    def charger_parametres(self) -> dict[str, float]:
        cur = self._executer("SELECT code, valeur FROM dbo.parametre")
        base = {
            "FACTEUR_PANNEAU_PRATIQUE": 0.4,
            "FACTEUR_PANNEAU_SOIR": 0.5,
            "FACTEUR_MARGE_BATTERIE": 1.5,
            "DUREE_MATIN_H": 11.0,
        }
        for code, valeur in cur.fetchall():
            base[str(code)] = float(valeur)
        return base

    def creer_simulation(self, titre: str, notes: str | None) -> int:
        cur = self._executer(
            """
            INSERT INTO dbo.simulation (titre, notes)
            OUTPUT INSERTED.id
            VALUES (?, ?)
            """,
            [titre, notes],
        )
        simulation_id = int(cur.fetchone()[0])
        self.cnxn.commit()
        return simulation_id

    def supprimer_simulation(self, simulation_id: int):
        self._executer("DELETE FROM dbo.simulation_entree WHERE simulation_id = ?", [simulation_id])
        self._executer("DELETE FROM dbo.simulation WHERE id = ?", [simulation_id])
        self.cnxn.commit()

    def lister_entrees(self, simulation_id: int) -> list[EntreeSimulation]:
        cur = self._executer(
            """
            SELECT se.id, se.simulation_id, se.materiel, se.puissance_w, se.id_tranche_heure, th.libelle, se.duree_h
            FROM dbo.simulation_entree se
            INNER JOIN dbo.tranche_heure th ON th.id = se.id_tranche_heure
            WHERE se.simulation_id = ?
            ORDER BY se.id
            """,
            [simulation_id],
        )
        return [
            EntreeSimulation(
                id=int(r[0]),
                simulation_id=int(r[1]),
                materiel=str(r[2]),
                puissance_w=float(r[3]),
                id_tranche_heure=int(r[4]),
                tranche=str(r[5]),
                duree_h=float(r[6]),
            )
            for r in cur.fetchall()
        ]

    def ajouter_entree(
        self,
        simulation_id: int,
        materiel: str,
        puissance_w: float,
        id_tranche_heure: int,
        duree_h: float,
    ):
        self._executer(
            """
            INSERT INTO dbo.simulation_entree
            (simulation_id, materiel, puissance_w, id_tranche_heure, duree_h)
            VALUES (?, ?, ?, ?, ?)
            """,
            [simulation_id, materiel, puissance_w, id_tranche_heure, duree_h],
        )
        self.cnxn.commit()

    def modifier_entree(
        self,
        entree_id: int,
        materiel: str,
        puissance_w: float,
        id_tranche_heure: int,
        duree_h: float,
    ):
        self._executer(
            """
            UPDATE dbo.simulation_entree
            SET materiel = ?, puissance_w = ?, id_tranche_heure = ?, duree_h = ?
            WHERE id = ?
            """,
            [materiel, puissance_w, id_tranche_heure, duree_h, entree_id],
        )
        self.cnxn.commit()

    def supprimer_entree(self, entree_id: int):
        self._executer("DELETE FROM dbo.simulation_entree WHERE id = ?", [entree_id])
        self.cnxn.commit()

    def commit(self):
        if self.cnxn is not None:
            self.cnxn.commit()

    def rollback(self):
        if self.cnxn is not None:
            self.cnxn.rollback()
