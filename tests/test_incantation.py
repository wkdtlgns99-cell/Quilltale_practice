import pytest
from src.world.state import Player
from src.world.incantation import IncantationSystem
from src.core.config import BASE_INCANTATION_CHARS, WISDOM_INCANT_BONUS

def test_get_char_limit_base():
    player = Player()
    player.wisdom = 10
    assert IncantationSystem.get_char_limit(player) == BASE_INCANTATION_CHARS

def test_get_char_limit_bonus():
    player = Player()
    player.wisdom = 12
    assert IncantationSystem.get_char_limit(player) == BASE_INCANTATION_CHARS + WISDOM_INCANT_BONUS * (12 - 10)

def test_validate_incantation_too_long():
    player = Player()
    player.wisdom = 10
    limit = IncantationSystem.get_char_limit(player)
    spell_text = "a" * (limit + 1)
    is_valid, reason = IncantationSystem.validate_incantation(player, spell_text)
    assert is_valid is False
    assert "너무 깁니다" in reason

def test_validate_incantation_unknown_words():
    player = Player()
    player.wisdom = 10
    spell_text = "test"
    is_valid, reason = IncantationSystem.validate_incantation(player, spell_text, ["unknown_word"])
    assert is_valid is False
    assert "아직 습득하지 못한 마법 언어" in reason

def test_validate_incantation_valid():
    player = Player()
    player.wisdom = 10
    spell_text = "test"
    player.known_magic_words.append("known")
    is_valid, reason = IncantationSystem.validate_incantation(player, spell_text, ["known"])
    assert is_valid is True
    assert reason == ""

def test_detect_incantation_in_action():
    assert IncantationSystem.detect_incantation_in_action("마법을 시전한다") is True
    assert IncantationSystem.detect_incantation_in_action("영창을 시작한다") is True
    assert IncantationSystem.detect_incantation_in_action("이그니스 사기타 볼란스!") is True
    assert IncantationSystem.detect_incantation_in_action("검을 휘두른다") is False

def test_parse_3slot_incantation():
    res = IncantationSystem.parse_incantation("이그니스 사기타 볼란스")
    assert res is not None
    assert res["type"] == "modular"
    assert "이그니스" in res["elements"]
    assert "사기타" in res["forms"]
    assert "볼란스" in res["vectors"]
    assert res["power_mult"] == 1.0
    assert "화염" in res["description_summary"]
    assert "화살" in res["description_summary"]

def test_parse_4slot_amplified_incantation():
    res = IncantationSystem.parse_incantation("암플리피코 이그니스 스페라 임팩투스")
    assert res is not None
    assert res["type"] == "modular"
    assert "암플리피코" in res["modifiers"]
    assert "이그니스" in res["elements"]
    assert "스페라" in res["forms"]
    assert "임팩투스" in res["vectors"]
    assert res["power_mult"] == 2.0  # Amplifico multiplies power by 2.0
    assert res["mana_cost"] >= 25

def test_parse_pact_incantation():
    res = IncantationSystem.parse_incantation("상구이스 샬라 아우라")
    assert res is not None
    assert res["type"] == "pact"
    assert res["cost_type"] == "hp"
    assert "화염 군주" in res["pact_god"]
    assert res["power_mult"] == 2.5

def test_classify_magic_words():
    words = ["이그니스", "사기타", "볼란스", "암플리피코", "상구이스", "미지의단어"]
    classified = IncantationSystem.classify_magic_words(words)
    assert len(classified["elements"]) == 1
    assert classified["elements"][0]["word"] == "이그니스"
    assert len(classified["forms"]) == 1
    assert classified["forms"][0]["word"] == "사기타"
    assert len(classified["vectors"]) == 1
    assert classified["vectors"][0]["word"] == "볼란스"
    assert len(classified["modifiers"]) == 1
    assert classified["modifiers"][0]["word"] == "암플리피코"
    assert len(classified["pacts"]) == 1
    assert classified["pacts"][0]["word"] == "상구이스"
    assert len(classified["custom"]) == 1
    assert classified["custom"][0]["word"] == "미지의단어"

