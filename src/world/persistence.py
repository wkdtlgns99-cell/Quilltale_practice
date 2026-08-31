"""
Session Persistence Manager for Quilltale TRPG Engine.
Saves and restores WorldState snapshots to prevent data loss on browser refresh.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict
from src.core.config import SAVES_DIR
from .state import WorldState

logger = logging.getLogger(__name__)


class PersistenceManager:
    @staticmethod
    def get_save_path(session_id: str) -> Path:
        clean_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))
        return SAVES_DIR / f"{clean_id}.json"

    @classmethod
    def save_session(cls, state: WorldState) -> bool:
        """Save a WorldState instance to disk JSON."""
        try:
            filepath = cls.get_save_path(state.session_id)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(state.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to save session '{state.session_id}': {e}")
            return False

    @classmethod
    def load_session(cls, session_id: str) -> Optional[WorldState]:
        """Load a WorldState from disk JSON if exists."""
        filepath = cls.get_save_path(session_id)
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return WorldState.from_json(f.read())
        except Exception as e:
            logger.error(f"Failed to load session '{session_id}': {e}")
            return None

    @classmethod
    def list_saved_sessions(cls) -> List[Dict[str, str]]:
        """List all saved sessions with turn count and modified time."""
        results = []
        if not SAVES_DIR.exists():
            return results

        for p in SAVES_DIR.glob("*.json"):
            if p.name.endswith('_manual.json'):
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    results.append({
                        "session_id": data.get("session_id", p.stem),
                        "world_name": data.get("world_name", "Unknown"),
                        "turn": str(data.get("turn", 0)),
                        "file_path": str(p),
                    })
            except Exception:
                continue
        return results

    @classmethod
    def manual_save(cls, state: WorldState) -> str:
        """Manually save current state to world-specific slot. Returns save path."""
        world_id = getattr(state, 'world_id', state.session_id)
        save_path = SAVES_DIR / f'{world_id}_manual.json'
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(state.to_json())
        return str(save_path)

    @classmethod  
    def load_manual_save(cls, world_id: str) -> Optional[WorldState]:
        """Load the manual save for a specific world."""
        save_path = SAVES_DIR / f'{world_id}_manual.json'
        if not save_path.exists():
            return None
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                return WorldState.from_json(f.read())
        except Exception as e:
            logger.error(f'Manual load failed: {e}')
            return None

    @classmethod
    def list_saved_worlds(cls) -> list[dict]:
        """List all saved world sessions."""
        results = []
        if not SAVES_DIR.exists():
            return results
        for p in SAVES_DIR.glob('*_manual.json'):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                results.append({
                    'world_id': data.get('world_id', 'unknown'),
                    'world_name': data.get('world_name', '알 수 없는 세계'),
                    'world_genre': data.get('world_genre', ''),
                    'player_name': data.get('player', {}).get('name', '방랑자'),
                    'turn': data.get('turn', 0),
                    'save_path': str(p),
                })
            except Exception:
                pass
        return results

    @classmethod
    def delete_manual_save(cls, world_id: str) -> bool:
        """Delete manual save file and associated auto-save for a world."""
        if not world_id:
            return False
        deleted = False
        save_path = SAVES_DIR / f"{world_id}_manual.json"
        if save_path.exists():
            try:
                save_path.unlink()
                deleted = True
            except Exception as e:
                logger.error(f"Failed to delete save {save_path}: {e}")
        auto_path = SAVES_DIR / f"{world_id}.json"
        if auto_path.exists():
            try:
                auto_path.unlink()
                deleted = True
            except Exception:
                pass
        return deleted

