"""
Unified Memory Manager for Quilltale TRPG Engine.
Orchestrates Vector Store, Jina Embeddings, Episodic Memory (1-5 significance),
and World Lore/Rumors for deep RAG retrieval.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional
from src.core.config import QDRANT_PATH, QDRANT_URL, JINA_MODEL, EMBEDDING_DIMENSION
from .base import BaseVectorStore, BaseEmbedder, SearchResult
from .embeddings import BGEM3Embedder, get_default_embedder
from .qdrant_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Manages long-term episodic memories, world rumors, and lore.
    Provides metadata-filtered semantic search for 100+ turn sessions.
    """

    COLLECTION_EPISODIC = "qt_episodic_memory"
    COLLECTION_LORE = "qt_world_lore"
    COLLECTION_REGION_TEMPLATES = "qt_region_templates"
    COLLECTION_ARCANE_TEMPLATES = "qt_arcane_templates"
    COLLECTION_REALISM_TEMPLATES = "qt_realism_templates"
    COLLECTION_MONSTER_TEMPLATES = "qt_monster_templates"

    def __init__(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        embedder: Optional[BaseEmbedder] = None,
    ):
        if vector_store is not None:
            self.store = vector_store
        else:
            if QDRANT_URL:
                self.store = QdrantVectorStore(url=QDRANT_URL)
            else:
                self.store = QdrantVectorStore(path=QDRANT_PATH)

        self.embedder = embedder or get_default_embedder()

        # Initialize collections
        self.store.ensure_collection(self.COLLECTION_EPISODIC, EMBEDDING_DIMENSION)
        self.store.ensure_collection(self.COLLECTION_LORE, EMBEDDING_DIMENSION)
        self.store.ensure_collection(self.COLLECTION_REGION_TEMPLATES, EMBEDDING_DIMENSION)
        self.store.ensure_collection(self.COLLECTION_ARCANE_TEMPLATES, EMBEDDING_DIMENSION)
        self.store.ensure_collection(self.COLLECTION_REALISM_TEMPLATES, EMBEDDING_DIMENSION)
        self.store.ensure_collection(self.COLLECTION_MONSTER_TEMPLATES, EMBEDDING_DIMENSION)

    def index_region_templates(self, templates_path: Optional[Any] = None) -> int:
        """
        Index all 30 deep region templates into Qdrant vector database for RAG retrieval.
        Returns the count of indexed templates.
        """
        import json
        from pathlib import Path
        from src.core.config import TEMPLATES_DIR
        
        path = templates_path or (TEMPLATES_DIR / "region_templates.json")
        if not Path(path).exists():
            logger.warning(f"Region templates file not found: {path}")
            return 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                templates = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load region templates: {e}")
            return 0

        count = 0
        for reg in templates:
            rid = reg.get("id", str(uuid.uuid4()))
            name = reg.get("name", "미지의 지역")
            genres = ", ".join(reg.get("genre_tags", []))
            elements = ", ".join(reg.get("element_tags", []))
            env = reg.get("environment", "")
            origin = reg.get("origin_event", "")
            twist = reg.get("hidden_twist", "")
            
            search_text = (
                f"[지역: {name}] 장르: {genres} | 속성: {elements} | "
                f"환경: {env} | 기원: {origin} | 비밀: {twist}"
            )
            
            vectors = self.embedder.embed_passages([search_text])
            if not vectors:
                continue
            vector = vectors[0]
            
            payload = {
                "id": rid,
                "name": name,
                "genre_tags": reg.get("genre_tags", []),
                "element_tags": reg.get("element_tags", []),
                "environment": env,
                "origin_event": origin,
                "entrance_hook": reg.get("entrance_hook", ""),
                "hidden_twist": twist,
                "ticking_clock": reg.get("ticking_clock", ""),
                "point_of_no_return": reg.get("point_of_no_return", ""),
                "core_dilemma": reg.get("core_dilemma", ""),
                "bread_crumb_trail": reg.get("bread_crumb_trail", []),
                "world_consequence": reg.get("world_consequence", ""),
                "environmental_gimmicks": reg.get("environmental_gimmicks", ""),
                "survival_hazards": reg.get("survival_hazards", ""),
                "faction_dynamics": reg.get("faction_dynamics", ""),
                "flora_fauna_crafting": reg.get("flora_fauna_crafting", ""),
                "dynamic_disasters": reg.get("dynamic_disasters", ""),
                "local_economy_taboo": reg.get("local_economy_taboo", ""),
                "corruption_mutation_meter": reg.get("corruption_mutation_meter", ""),
                "dynamic_terraforming": reg.get("dynamic_terraforming", ""),
                "local_rituals_minigames": reg.get("local_rituals_minigames", ""),
                "environmental_boss_gimmicks": reg.get("environmental_boss_gimmicks", ""),
                "linguistic_curse_syntax": reg.get("linguistic_curse_syntax", ""),
                "environmental_esp": reg.get("environmental_esp", ""),
                "macro_entity_negotiation": reg.get("macro_entity_negotiation", ""),
                "cascading_domino_effect": reg.get("cascading_domino_effect", ""),
                "death_rites_scars": reg.get("death_rites_scars", ""),
                "search_text": search_text,
                "type": "region_template"
            }
            
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"region_template_{rid}"))
            if self.store.upsert(self.COLLECTION_REGION_TEMPLATES, point_id, vector, payload):
                count += 1

        logger.info(f"Indexed {count} region templates into Qdrant collection '{self.COLLECTION_REGION_TEMPLATES}'")
        return count


    def index_arcane_templates(self, templates_path: Optional[Any] = None) -> int:
        """
        Index 10 Fantasy Biomechanics & Arcane Physics templates into Qdrant vector memory.
        """
        import json
        from src.core.config import TEMPLATES_DIR
        path = templates_path or (TEMPLATES_DIR / "arcane_physics_template.json")
        if not path.exists():
            logger.warning(f"Arcane physics template file not found at {path}")
            return 0

        with open(path, "r", encoding="utf-8") as f:
            templates = json.load(f)

        count = 0
        for item in templates:
            aid = item.get("id", f"arcane_{count}")
            search_text = (
                f"{item.get('name', '')} {item.get('category', '')} {item.get('core_principle', '')} "
                f"{' '.join(item.get('symptoms', []))} {item.get('mechanical_effect', '')}"
            )
            vectors = self.embedder.embed_passages([search_text])
            if not vectors:
                continue
            vector = vectors[0]
            payload = {
                "id": aid,
                "name": item.get("name", ""),
                "category": item.get("category", ""),
                "core_principle": item.get("core_principle", ""),
                "symptoms": item.get("symptoms", []),
                "mechanical_effect": item.get("mechanical_effect", ""),
                "search_text": search_text,
                "type": "arcane_template"
            }
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"arcane_template_{aid}"))
            if self.store.upsert(self.COLLECTION_ARCANE_TEMPLATES, point_id, vector, payload):
                count += 1
        logger.info(f"Indexed {count} arcane physics templates into Qdrant collection '{self.COLLECTION_ARCANE_TEMPLATES}'")
        return count

    def search_arcane_templates(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant arcane physics templates using Qdrant vector similarity."""
        if not query.strip():
            return []
        query_vector = self.embedder.embed_query(query)
        results = self.store.search(
            self.COLLECTION_ARCANE_TEMPLATES,
            query_vector=query_vector,
            limit=limit,
        )
        return [r.payload for r in results]

    def index_realism_templates(self, templates_path: Optional[Any] = None) -> int:
        """
        Index 15 Realism & Causality Mechanics templates into Qdrant vector memory.
        """
        import json
        from src.core.config import TEMPLATES_DIR
        path = templates_path or (TEMPLATES_DIR / "realism_mechanics_template.json")
        if not path.exists():
            logger.warning(f"Realism mechanics template file not found at {path}")
            return 0

        with open(path, "r", encoding="utf-8") as f:
            templates = json.load(f)

        count = 0
        for item in templates:
            rid = item.get("id", f"realism_{count}")
            search_text = (
                f"{item.get('name', '')} {item.get('category', '')} {item.get('core_principle', '')} "
                f"{' '.join(item.get('triggers', []))} {' '.join(item.get('consequences', []))}"
            )
            vectors = self.embedder.embed_passages([search_text])
            if not vectors:
                continue
            vector = vectors[0]
            payload = {
                "id": rid,
                "name": item.get("name", ""),
                "category": item.get("category", ""),
                "core_principle": item.get("core_principle", ""),
                "triggers": item.get("triggers", []),
                "consequences": item.get("consequences", []),
                "search_text": search_text,
                "type": "realism_template"
            }
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"realism_template_{rid}"))
            if self.store.upsert(self.COLLECTION_REALISM_TEMPLATES, point_id, vector, payload):
                count += 1
        logger.info(f"Indexed {count} realism templates into Qdrant collection '{self.COLLECTION_REALISM_TEMPLATES}'")
        return count



    def index_monster_templates(self, templates_path: Optional[Any] = None) -> int:
        """
        Index 15 Elite/Boss Gimmick Monster templates into Qdrant vector memory.
        """
        import json
        from src.core.config import TEMPLATES_DIR
        path = templates_path or (TEMPLATES_DIR / "monster_templates.json")
        if not path.exists():
            logger.warning(f"Monster templates file not found at {path}")
            return 0

        with open(path, "r", encoding="utf-8") as f:
            templates = json.load(f)

        count = 0
        for item in templates:
            mid = item.get("id", f"monster_{count}")
            search_text = (
                f"{item.get('name', '')} {item.get('tier', '')} {item.get('concept_theme', '')} "
                f"{item.get('origin_lore', '')} {item.get('visual_anatomy', '')} {item.get('weakness_exploit', '')}"
            )
            vectors = self.embedder.embed_passages([search_text])
            if not vectors:
                continue
            vector = vectors[0]
            payload = {
                "id": mid,
                "name": item.get("name", ""),
                "tier": item.get("tier", "elite"),
                "concept_theme": item.get("concept_theme", ""),
                "origin_lore": item.get("origin_lore", ""),
                "visual_anatomy": item.get("visual_anatomy", ""),
                "observation_clue": item.get("observation_clue", ""),
                "stat_profile": item.get("stat_profile", {}),
                "combat_patterns": item.get("combat_patterns", []),
                "boss_skills": item.get("boss_skills", {}),
                "weakness_exploit": item.get("weakness_exploit", ""),
                "drops_and_materials": item.get("drops_and_materials", []),
                "extractable_skill": item.get("extractable_skill", {}),
                "dialogue_tone": item.get("dialogue_tone", ""),
                "voice_lines": item.get("voice_lines", {}),
                "death_aftermath": item.get("death_aftermath", ""),
                "search_text": search_text,
                "type": "monster_template"
            }
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"monster_template_{mid}"))
            if self.store.upsert(self.COLLECTION_MONSTER_TEMPLATES, point_id, vector, payload):
                count += 1
        logger.info(f"Indexed {count} monster templates into Qdrant collection '{self.COLLECTION_MONSTER_TEMPLATES}'")
        return count

    def search_monster_templates(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant monster templates using Qdrant vector similarity."""
        if not query.strip():
            return []
        query_vector = self.embedder.embed_query(query)
        results = self.store.search(
            self.COLLECTION_MONSTER_TEMPLATES,
            query_vector=query_vector,
            limit=limit,
        )
        return [r.payload for r in results]

    def search_realism_templates(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Search for relevant realism mechanics templates using Qdrant vector similarity."""
        if not query.strip():
            return []
        query_vector = self.embedder.embed_query(query)
        results = self.store.search(
            self.COLLECTION_REALISM_TEMPLATES,
            query_vector=query_vector,
            limit=limit,
        )
        return [r.payload for r in results]

    def search_region_templates(
        self,
        query: str,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Search for most relevant region templates using Qdrant vector similarity.
        Returns list of region template payloads.
        """
        if not query.strip():
            return []

        query_vector = self.embedder.embed_query(query)
        results = self.store.search(
            self.COLLECTION_REGION_TEMPLATES,
            query_vector=query_vector,
            limit=limit,
        )
        return [r.payload for r in results]


    def record_turn_memory(
        self,
        session_id: str,
        turn: int,
        action: str,
        narration: str,
        location_id: str,
        npc_ids: Optional[List[str]] = None,
        significance: int = 1,
        emotional_tone: str = "neutral",
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Index a single turn interaction into Qdrant vector memory.
        Significance scale: 1 (minor) ~ 5 (world-shaking / permanently anchored).
        """
        npc_ids = npc_ids or []
        tags = tags or []
        is_anchor = significance >= 4

        memory_text = (
            f"[턴 {turn} | 위치: {location_id}] "
            f"행동: {action} → 결과: {narration}"
        )

        # Generate embedding vector
        vectors = self.embedder.embed_passages([memory_text])
        if not vectors:
            return False
        vector = vectors[0]

        payload = {
            "session_id": session_id,
            "turn": turn,
            "action": action,
            "narration": narration,
            "location_id": location_id,
            "npc_ids": npc_ids,
            "significance": significance,
            "emotional_tone": emotional_tone,
            "is_anchor": is_anchor,
            "tags": tags,
            "text": memory_text,
            "type": "episodic",
        }

        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{session_id}_turn_{turn}"))
        return self.store.upsert(self.COLLECTION_EPISODIC, point_id, vector, payload)

    def index_lore(
        self,
        lore_id: str,
        title: str,
        content: str,
        location_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """
        Index encyclopedic world lore or global rumors into vector memory.
        """
        tags = tags or []
        lore_text = f"[{title}] {content}"
        vectors = self.embedder.embed_passages([lore_text])
        if not vectors:
            return False
        vector = vectors[0]

        payload = {
            "lore_id": lore_id,
            "title": title,
            "content": content,
            "location_id": location_id,
            "tags": tags,
            "text": lore_text,
            "type": "lore",
        }

        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"lore_{lore_id}"))
        return self.store.upsert(self.COLLECTION_LORE, point_id, vector, payload)

    def retrieve_context(
        self,
        session_id: str,
        current_action: str,
        current_location: str,
        current_npcs: Optional[List[str]] = None,
        top_k: int = 4,
    ) -> str:
        """
        Hybrid retrieval combining semantic similarity and session filtering.
        Returns a formatted Korean markdown block for GM prompt synthesis.
        """
        if not current_action.strip():
            return "관련된 과거 장기 기억 없음."

        query_vector = self.embedder.embed_query(current_action)

        # 1. Retrieve relevant episodic memories for this session
        episodic_filters = {"session_id": session_id}
        episodic_results = self.store.search(
            self.COLLECTION_EPISODIC,
            query_vector=query_vector,
            limit=top_k,
            filters=episodic_filters,
        )

        # 2. Retrieve relevant world lore / rumors
        lore_results = self.store.search(
            self.COLLECTION_LORE,
            query_vector=query_vector,
            limit=2,
        )

        lines = []

        if episodic_results:
            lines.append("### 📜 관련 과거 사건 및 인과 관계 (RAG 기억):")
            for r in episodic_results:
                p = r.payload
                sig = p.get("significance", 1)
                anchor_tag = " [영구 보존된 핵심 사건]" if p.get("is_anchor") else ""
                lines.append(
                    f"  - (턴 {p.get('turn', '?')}, 중요도 {sig}/5{anchor_tag}): {p.get('text', '')}"
                )

        if lore_results:
            lines.append("### 📚 관련 세계관 설정 및 소문:")
            for r in lore_results:
                lines.append(f"  - {r.text}")

        if not lines:
            return "관련된 과거 장기 기억 없음."

        return "\n".join(lines)

    def retrieve_graph_context(
        self,
        action: str,
        location_name: str,
        location_id: str,
        inventory_items: Optional[List[str]] = None,
        monsters: Optional[List[str]] = None,
    ) -> str:
        """
        Retrieve Knowledge Graph relations, Physics & Chemistry laws, and Cross-regional synergies.
        Returns a formatted Korean markdown block for GM prompt synthesis.
        """
        from src.world.graph_engine import LivingWorldGraph, PhysicsChemistryMatrix
        
        inventory_items = inventory_items or []
        monsters = monsters or []
        graph = LivingWorldGraph()
        
        lines = []
        
        # 1. Physical & Chemical interaction evaluation for current action
        interaction = PhysicsChemistryMatrix.evaluate_interaction(action, f"{location_name} {' '.join(monsters)}")
        if interaction:
            lines.append("### 🧪 물리·화학적 상호작용 법칙 (Physics/Chemistry Matrix):")
            lines.append(f"  - **[반응 법칙: {interaction['result_name']}]** (위력 계수: x{interaction['damage_bonus']})")
            lines.append(f"  - 인과 원리: {interaction['description']}")

        # 2. Regional ecosystem graph facts
        ecosystem = graph.get_regional_ecosystem(location_id)
        if ecosystem:
            lines.append(f"### 🕸️ {ecosystem['region_name']} 생태계 지식 그래프 (GraphRAG):")
            lines.append(f"  - 지배 원소: {', '.join(ecosystem.get('dominant_elements', []))}")
            lines.append(f"  - 토착 부족/종족: {', '.join(ecosystem.get('native_races', []))}")
            if ecosystem.get('monsters'):
                for m in ecosystem['monsters']:
                    lines.append(f"  - 고유 마수: [{m['name']}] (약점: {', '.join(m.get('weakness', []))} | 내성: {', '.join(m.get('resistance', []))})")
                    lines.append(f"    ↳ 전리품 소재: {m.get('material_drop')} ➔ 제작 장비: {m.get('craftable_item')}")

        # 3. Cross-regional item synergies
        synergies = graph.find_cross_regional_synergies(inventory_items, location_name, monsters)
        if synergies:
            lines.append("### 🔄 타 지역 아이템-환경 교차 시너지 (Cross-Regional Synergy):")
            for syn in synergies:
                r = syn['rule']
                lines.append(f"  - 소지품 [{syn['item']}] ↔ 대상 [{syn['target']}]: {r['result_name']} 발생 가능 ({r['description']})")

        return "\n".join(lines) if lines else ""

