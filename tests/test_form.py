import os
from src.VibeCForms import read_forms, write_forms, DATA_FILE

def test_write_and_read_forms(tmp_path):
    test_file = tmp_path / "registros.txt"
    forms = [
        {"nome": "Ana", "telefone": "123", "whatsapp": True},
        {"nome": "Bob", "telefone": "456", "whatsapp": False}
    ]
    # Temporariamente altera o DATA_FILE
    orig_file = DATA_FILE
    try:
        globals()["DATA_FILE"] = str(test_file)
        write_forms(forms)
        result = read_forms()
        assert result == forms
    finally:
        globals()["DATA_FILE"] = orig_file

def test_update_form(tmp_path):
    test_file = tmp_path / "registros.txt"
    forms = [
        {"nome": "Ana", "telefone": "123", "whatsapp": True},
        {"nome": "Bob", "telefone": "456", "whatsapp": False}
    ]
    orig_file = DATA_FILE
    try:
        globals()["DATA_FILE"] = str(test_file)
        write_forms(forms)
        # Altera o telefone de Ana
        forms[0]["telefone"] = "999"
        write_forms(forms)
        result = read_forms()
        assert result[0]["telefone"] == "999"
    finally:
        globals()["DATA_FILE"] = orig_file

def test_delete_form(tmp_path):
    test_file = tmp_path / "registros.txt"
    forms = [
        {"nome": "Ana", "telefone": "123", "whatsapp": True},
        {"nome": "Bob", "telefone": "456", "whatsapp": False}
    ]
    orig_file = DATA_FILE
    try:
        globals()["DATA_FILE"] = str(test_file)
        write_forms(forms)
        # Remove Bob
        forms = [c for c in forms if c["nome"] != "Bob"]
        write_forms(forms)
        result = read_forms()
        assert len(result) == 1
        assert result[0]["nome"] == "Ana"
    finally:
        globals()["DATA_FILE"] = orig_file
