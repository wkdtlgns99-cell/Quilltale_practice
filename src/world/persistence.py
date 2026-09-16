"""
Session Persistence Manager for Quilltale TRPG Engine.
Saves and restores WorldState snapshots to prevent data loss on browser refresh.
Now uses SQLite3 Document Store pattern instead of raw JSON files.
"""
import json
import sqlite3
import logging
from typing import Optional
from src.core.config import SAVES_DIR
from .state import WorldState

logger = logging.getLogger(__name__)

class PersistenceManager:
    DB_PATH = SAVES_DIR / "quilltale.db"

    @classmethod
    def _init_db(cls):
        if not SAVES_DIR.exists():
            SAVES_DIR.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(cls.DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS save_slots (
                    world_id TEXT PRIMARY KEY,
                    world_name TEXT,
                    player_name TEXT,
                    turn INTEGER,
                    is_manual BOOLEAN,
                    state_data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS turn_history_archive (
                    world_id TEXT,
                    turn INTEGER,
                    action TEXT,
                    narration TEXT,
                    turn_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (world_id, turn)
                )
            """)
            conn.commit()

    @classmethod
    def save_session(cls, state: WorldState) -> bool:
        """Save a WorldState instance to SQLite DB (Auto Save)."""
        cls._init_db()
        try:
            world_id = getattr(state, 'world_id', state.session_id)
            world_name = state.world_name
            player_name = state.player.name if hasattr(state, 'player') and state.player else "방랑자"
            turn = state.turn
            state_data = state.to_json()

            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO save_slots (world_id, world_name, player_name, turn, is_manual, state_data, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(world_id) DO UPDATE SET
                        world_name=excluded.world_name,
                        player_name=excluded.player_name,
                        turn=excluded.turn,
                        state_data=excluded.state_data,
                        updated_at=CURRENT_TIMESTAMP
                """, (f"{world_id}_auto", world_name, player_name, turn, False, state_data))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to save session '{state.session_id}': {e}")
            return False

    @classmethod
    def load_session(cls, session_id: str) -> Optional[WorldState]:
        """Load a WorldState from SQLite DB (Auto Save)."""
        cls._init_db()
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT state_data FROM save_slots WHERE world_id = ?", (f"{session_id}_auto",))
                row = cursor.fetchone()
                if row:
                    return WorldState.from_json(row[0])
            return None
        except Exception as e:
            logger.error(f"Failed to load session '{session_id}': {e}")
            return None

    @classmethod
    def manual_save(cls, state: WorldState) -> str:
        """Manually save current state to SQLite DB."""
        cls._init_db()
        try:
            world_id = getattr(state, 'world_id', state.session_id)
            world_name = state.world_name
            player_name = state.player.name if hasattr(state, 'player') and state.player else "방랑자"
            turn = state.turn
            state_data = state.to_json()

            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO save_slots (world_id, world_name, player_name, turn, is_manual, state_data, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(world_id) DO UPDATE SET
                        world_name=excluded.world_name,
                        player_name=excluded.player_name,
                        turn=excluded.turn,
                        state_data=excluded.state_data,
                        updated_at=CURRENT_TIMESTAMP
                """, (f"{world_id}_manual", world_name, player_name, turn, True, state_data))
                conn.commit()
            return f"sqlite://{cls.DB_PATH}/{world_id}_manual"
        except Exception as e:
            logger.error(f"Failed to manual save '{world_id}': {e}")
            return ""

    @classmethod  
    def load_manual_save(cls, world_id: str) -> Optional[WorldState]:
        """Load the manual save for a specific world from SQLite DB."""
        cls._init_db()
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT state_data FROM save_slots WHERE world_id = ?", (f"{world_id}_manual",))
                row = cursor.fetchone()
                if row:
                    return WorldState.from_json(row[0])
            return None
        except Exception as e:
            logger.error(f"Manual load failed: {e}")
            return None

    @classmethod
    def list_saved_worlds(cls) -> list[dict]:
        """List all saved world sessions (manual saves) from SQLite."""
        cls._init_db()
        results = []
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT world_id, world_name, player_name, turn FROM save_slots WHERE is_manual = 1 ORDER BY updated_at DESC")
                for row in cursor.fetchall():
                    wid = row[0].replace("_manual", "")
                    results.append({
                        'world_id': wid,
                        'world_name': row[1],
                        'world_genre': '',
                        'player_name': row[2],
                        'turn': row[3],
                        'save_path': f"sqlite://{cls.DB_PATH}/{row[0]}",
                    })
        except Exception as e:
            logger.error(f"Failed to list saved worlds: {e}")
        return results

    @classmethod
    def delete_manual_save(cls, world_id: str) -> bool:
        """Delete manual and auto saves from SQLite."""
        cls._init_db()
        if not world_id:
            return False
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM save_slots WHERE world_id IN (?, ?)", (f"{world_id}_manual", f"{world_id}_auto"))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete save {world_id}: {e}")
            return False

    @classmethod
    def archive_turns(cls, world_id: str, turns: list[dict]) -> int:
        """Archive turn history entries to SQLite turn_history_archive table."""
        if not turns:
            return 0
        cls._init_db()
        archived_count = 0
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                for t in turns:
                    turn_num = t.get("turn", 0)
                    action = t.get("action", "")
                    narration = t.get("narration", "")
                    data_json = json.dumps(t, ensure_ascii=False)
                    cursor.execute("""
                        INSERT INTO turn_history_archive (world_id, turn, action, narration, turn_data, created_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(world_id, turn) DO UPDATE SET
                            action=excluded.action,
                            narration=excluded.narration,
                            turn_data=excluded.turn_data,
                            created_at=CURRENT_TIMESTAMP
                    """, (world_id, turn_num, action, narration, data_json))
                    archived_count += 1
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to archive turns for '{world_id}': {e}")
        return archived_count

    @classmethod
    def get_archived_turns(cls, world_id: str) -> list[dict]:
        """Fetch all archived turns for a world sorted by turn ascending."""
        cls._init_db()
        results = []
        try:
            with sqlite3.connect(cls.DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT turn_data FROM turn_history_archive WHERE world_id = ? ORDER BY turn ASC",
                    (world_id,)
                )
                for row in cursor.fetchall():
                    try:
                        results.append(json.loads(row[0]))
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Failed to fetch archived turns for '{world_id}': {e}")
        return results

    @classmethod
    def get_full_history(cls, world_id: str, active_history: list[dict] | None = None) -> list[dict]:
        """Combine archived history and active history, deduplicated and sorted by turn."""
        archived = cls.get_archived_turns(world_id)
        turn_map = {}
        for item in archived:
            turn_map[item.get("turn")] = item
        if active_history:
            for item in active_history:
                turn_map[item.get("turn")] = item
        return sorted(turn_map.values(), key=lambda x: x.get("turn", 0))


