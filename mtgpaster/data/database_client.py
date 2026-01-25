import sqlite3
from typing import List, Tuple

from mtgpaster.api.api_client import ApiClient
from mtgpaster.api.api_error import ApiError
from mtgpaster.data.card_data import CardFace, CardData


class DatabaseClient:

    @staticmethod
    def get_connection(read_only: bool = False) -> sqlite3.Connection:
        """
        Returns the sqlite connection object for the Database.

        :return: sqlite3.Connection
        """

        return sqlite3.connect('card_data.db')


    @staticmethod
    def initialize() -> None:
        """
        Initializes the database, creating tables, populating with ScryFall data.

        :return: None
        """

        DatabaseClient.create_tables()

        api_response: list | ApiError = ApiClient.fetch_bulk_data()
        if isinstance(api_response, ApiError):
            print("Could not fetch bulk data.")
        if isinstance(api_response, list):
            print("Fetched bulk data from Scryfall...")
            DatabaseClient.parse_bulk_data(api_response)


    @staticmethod
    def create_tables() -> None:
        """
        Creates the database tables and triggers.

        :return: None
        """

        with DatabaseClient.get_connection() as connection:
            cursor = connection.cursor()

            try:
                cursor.executescript(
                    """
                        CREATE TABLE IF NOT EXISTS card_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            scryfall_id TEXT NOT NULL UNIQUE,
                            oracle_name TEXT NOT NULL,
                            oracle_text TEXT NOT NULL
                        );
                        
                        CREATE TABLE IF NOT EXISTS card_faces (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            scryfall_id TEXT NOT NULL UNIQUE,
                            side TEXT CHECK( side IN ('FRONT', 'BACK') ) NOT NULL DEFAULT 'FRONT',
                            thumbnail_url TEXT NOT NULL,
                            image_url TEXT NOT NULL,
                            
                            FOREIGN KEY (scryfall_id) REFERENCES card_data (scryfall_id)
                        );
                        
                        CREATE VIRTUAL TABLE IF NOT EXISTS card_data_fts USING fts5 (
                            scryfall_id,
                            oracle_name,
                            oracle_text
                        );
                        
                        CREATE TRIGGER IF NOT EXISTS card_data_insert AFTER INSERT ON card_data BEGIN 
                            INSERT INTO card_data_fts (scryfall_id, oracle_name, oracle_text) 
                            VALUES (new.scryfall_id, new.oracle_name, new.oracle_text);
                        END;
                    """
                )
            except sqlite3.Error as error:
                print(error)


    @staticmethod
    def parse_bulk_data(data: list) -> None:
        """
        Parses the bulk data import from the ScryFall API and inserts the data into the database.

        :param data: bulk data JSON from ScryFall.
        :return: None
        """

        card_data_list: List[CardData] = []

        for entry in data:
            if entry['image_status'] == "missing":
                continue

            if entry['layout'] == 'art_series':
                continue

            card_data: CardData = CardData(
                scryfall_id=entry['id'],
                oracle_name=entry['name'],
                oracle_text=entry['oracle_text'] if 'oracle_text' in entry else '',
            )

            if 'image_uris' in entry:  # Handling one-sided cards.
                card_data.faces.append(
                    CardFace(
                        scryfall_id=entry['id'],
                        image_url=entry['image_uris']['normal'],
                        thumbnail_url=entry['image_uris']['small'],
                        side='FRONT',
                    )
                )
            else:  # Handling two-sided cards.
                card_data.faces.append(
                    CardFace(
                        scryfall_id=entry['id'],
                        image_url=entry['card_faces'][0]['image_uris']['normal'],
                        thumbnail_url=entry['card_faces'][0]['image_uris']['small'],
                        side='FRONT'
                    )
                )
                card_data.faces.append(
                    CardFace(
                        scryfall_id=entry['id'],
                        image_url=entry['card_faces'][1]['image_uris']['normal'],
                        thumbnail_url=entry['card_faces'][1]['image_uris']['small'],
                        side='BACK'
                    )
                )

            card_data_list.append(card_data)

        DatabaseClient.insert_cards(card_data_list)


    @staticmethod
    def insert_cards(cards: List[CardData]) -> None:
        """
        Bulk inserts / updates card data into the database.

        :param cards: List of card data to insert.
        :return: None
        """
        with DatabaseClient.get_connection() as connection:
            cursor = connection.cursor()

            # Inserting general card data.
            card_data: List[Tuple] = []
            for card in cards:
                card_data.append((card.scryfall_id, card.oracle_name, card.oracle_text))

            cursor.executemany(
            """
                INSERT INTO card_data (scryfall_id, oracle_name, oracle_text) 
                VALUES (?, ?, ?)
                ON CONFLICT(scryfall_id) DO UPDATE SET 
                    oracle_name = excluded.oracle_name,
                    oracle_text = excluded.oracle_text
            """, card_data)

            # Inserting card face data.
            card_faces: List[Tuple] = []
            for card in cards:
                for face in card.faces:
                    card_faces.append(
                        (face.scryfall_id, face.side, face.thumbnail_url, face.image_url)
                    )

            cursor.executemany(
            """
                INSERT INTO card_faces (scryfall_id, side, thumbnail_url, image_url) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(scryfall_id) DO UPDATE SET 
                    side = excluded.side,
                    thumbnail_url = excluded.thumbnail_url,
                    image_url = excluded.image_url
            """, card_faces)


    @staticmethod
    def get_card_ids_fuzzy(text: str, offset: int = 0, limit: int = 6) -> List[str]:
        """
        Fetches a list of card scryfall_id from the database using fuzzy full text search matching.

        :param text: The text to search for.
        :param offset: Pagination row offset.
        :param limit: Limit of records to return per query.
        :return: List of scryfall_id strings.
        """

        with DatabaseClient.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA cache_size = 10000')

            cursor.row_factory = lambda c, row: row[0]

            cursor.execute("SELECT scryfall_id FROM card_data_fts WHERE card_data_fts = ? LIMIT ? OFFSET ?", [text, limit, offset])
            return cursor.fetchall()


    @staticmethod
    def get_card_faces(scryfall_id: str) -> List[CardFace]:
        """
        Returns the face(s) of one card.

        :param scryfall_id: The scryfall_id of the card to lookup.
        :return: List of CardFace objects.
        """
        with DatabaseClient.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA cache_size = 10000')

            cursor.row_factory = lambda c, row: CardFace(row[1], row[4], row[3], row[2])

            cursor.execute("SELECT * FROM card_faces WHERE scryfall_id = ?", [scryfall_id])
            return cursor.fetchall()