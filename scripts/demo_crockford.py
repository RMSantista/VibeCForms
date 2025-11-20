#!/usr/bin/env python3
"""
Script de demonstração do Sistema Crockford Base32.

Este script permite testar interativamente todas as funcionalidades
do sistema de IDs implementado na FASE 1.

Uso:
    python scripts/demo_crockford.py
"""

import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.crockford import (
    encode_uuid,
    decode_uuid,
    calculate_check_digit,
    generate_id,
    validate_id,
    normalize_id,
    get_uuid_from_id,
    ALPHABET,
)


def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_1_generate_ids():
    """Demonstração: Geração de IDs."""
    print_header("1. GERAÇÃO DE IDs")

    print("\n📝 Gerando 5 IDs novos:\n")
    for i in range(1, 6):
        new_id = generate_id()
        print(f"  {i}. {new_id}")

    print("\n✅ Todos os IDs têm 27 caracteres (26 UUID + 1 check digit)")
    print(f"✅ Caracteres válidos: {ALPHABET}")


def demo_2_encoding_decoding():
    """Demonstração: Encoding e Decoding."""
    print_header("2. ENCODING E DECODING DE UUID")

    # Create a known UUID
    test_uuid = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

    print(f"\n📌 UUID original:")
    print(f"   {test_uuid}")
    print(f"   Formato: {len(str(test_uuid))} caracteres (com hífens)")

    # Encode
    encoded = encode_uuid(test_uuid)
    print(f"\n🔄 Codificado em Crockford Base32:")
    print(f"   {encoded}")
    print(f"   Formato: {len(encoded)} caracteres (sem hífens)")

    # Calculate check digit
    check = calculate_check_digit(encoded)
    full_id = encoded + check
    print(f"\n➕ Com check digit:")
    print(f"   {full_id}")
    print(f"   └─ Check digit: '{check}'")

    # Decode back
    decoded = decode_uuid(full_id)
    print(f"\n🔙 Decodificado de volta:")
    print(f"   {decoded}")

    # Verify
    print(f"\n✅ Round-trip verificado: {decoded == test_uuid}")
    print(f"✅ Redução de tamanho: 36 → 27 caracteres ({((36-27)/36*100):.1f}% menor)")


def demo_3_validation():
    """Demonstração: Validação de IDs."""
    print_header("3. VALIDAÇÃO DE IDs")

    # Generate valid ID
    valid_id = generate_id()
    print(f"\n✅ ID válido:")
    print(f"   {valid_id}")
    print(f"   Validação: {validate_id(valid_id)}")

    # Test invalid length
    print(f"\n❌ ID com tamanho incorreto:")
    invalid_length = "CURTO123"
    print(f"   {invalid_length}")
    print(f"   Validação: {validate_id(invalid_length)}")

    # Test wrong checksum
    print(f"\n❌ ID com check digit incorreto:")
    wrong_check = valid_id[:-1] + ("0" if valid_id[-1] != "0" else "1")
    print(f"   {wrong_check}")
    print(f"   Validação: {validate_id(wrong_check)}")

    # Test invalid characters
    print(f"\n❌ ID com caracteres inválidos:")
    invalid_chars = "ABCDEFGHJKMNPQRSTVWXYZ012@"
    print(f"   {invalid_chars}")
    print(f"   Validação: {validate_id(invalid_chars)}")


def demo_4_normalization():
    """Demonstração: Normalização e tolerância a typos."""
    print_header("4. NORMALIZAÇÃO E TOLERÂNCIA A TYPOS")

    # Generate valid ID
    original = generate_id()
    print(f"\n📌 ID original (uppercase):")
    print(f"   {original}")

    # Test lowercase
    lowercase = original.lower()
    print(f"\n🔤 ID em lowercase:")
    print(f"   {lowercase}")
    print(f"   Validação: {validate_id(lowercase)}")
    normalized = normalize_id(lowercase)
    print(f"   Normalizado: {normalized}")
    print(f"   ✅ Aceito normalmente")

    # Test with typos (if ID contains replaceable chars)
    if "1" in original or "0" in original:
        typo_id = original.replace("1", "i", 1).replace("0", "o", 1)
        print(f"\n🔄 ID com typos comuns (1→i, 0→o):")
        print(f"   {typo_id}")
        print(f"   Validação: {validate_id(typo_id)}")
        normalized_typo = normalize_id(typo_id)
        print(f"   Normalizado: {normalized_typo}")
        print(f"   ✅ Typos corrigidos automaticamente")

    print(f"\n📋 Mapeamento de normalização:")
    print(f"   I, i, L, l → 1")
    print(f"   O, o       → 0")
    print(f"   U, u       → V")
    print(f"   lowercase  → UPPERCASE")


def demo_5_uuid_extraction():
    """Demonstração: Extração de UUID."""
    print_header("5. EXTRAÇÃO DE UUID DE ID")

    # Create ID from known UUID
    original_uuid = uuid.uuid4()
    encoded = encode_uuid(original_uuid)
    check = calculate_check_digit(encoded)
    full_id = encoded + check

    print(f"\n📌 UUID original:")
    print(f"   {original_uuid}")

    print(f"\n🔑 ID gerado:")
    print(f"   {full_id}")

    # Extract UUID
    extracted = get_uuid_from_id(full_id)
    print(f"\n🔓 UUID extraído:")
    print(f"   {extracted}")

    print(f"\n✅ Extração bem-sucedida: {extracted == original_uuid}")
    print(f"✅ Possibilita relacionamentos entre sistemas")


def demo_6_edge_cases():
    """Demonstração: Casos especiais."""
    print_header("6. CASOS ESPECIAIS")

    # Nil UUID
    nil_uuid = uuid.UUID("00000000-0000-0000-0000-000000000000")
    nil_encoded = encode_uuid(nil_uuid)
    nil_check = calculate_check_digit(nil_encoded)
    nil_id = nil_encoded + nil_check

    print(f"\n🔵 Nil UUID (all zeros):")
    print(f"   UUID: {nil_uuid}")
    print(f"   ID:   {nil_id}")
    print(f"   Validação: {validate_id(nil_id)}")

    # Max UUID
    max_uuid = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
    max_encoded = encode_uuid(max_uuid)
    max_check = calculate_check_digit(max_encoded)
    max_id = max_encoded + max_check

    print(f"\n🔴 Max UUID (all ones):")
    print(f"   UUID: {max_uuid}")
    print(f"   ID:   {max_id}")
    print(f"   Validação: {validate_id(max_id)}")

    print(f"\n✅ Sistema funciona corretamente em casos extremos")


def demo_7_performance():
    """Demonstração: Performance."""
    print_header("7. TESTE DE PERFORMANCE")

    import time

    # Generate IDs
    print(f"\n⚡ Gerando 1000 IDs únicos...")
    start = time.time()
    ids = [generate_id() for _ in range(1000)]
    elapsed = time.time() - start

    print(f"   Tempo: {elapsed*1000:.2f}ms")
    print(f"   Média: {elapsed*1000/1000:.3f}ms por ID")
    print(f"   Únicos: {len(set(ids))}/1000")

    # Validate IDs
    print(f"\n⚡ Validando 1000 IDs...")
    start = time.time()
    valid_count = sum(1 for id_str in ids if validate_id(id_str))
    elapsed = time.time() - start

    print(f"   Tempo: {elapsed*1000:.2f}ms")
    print(f"   Média: {elapsed*1000/1000:.3f}ms por validação")
    print(f"   Válidos: {valid_count}/1000")

    print(f"\n✅ Performance adequada para uso em produção")


def main():
    """Run all demonstrations."""
    print("\n" + "🎯" * 35)
    print("\n  DEMONSTRAÇÃO DO SISTEMA CROCKFORD BASE32 - FASE 1")
    print("  VibeCForms UUID ID System")
    print("\n" + "🎯" * 35)

    demos = [
        ("Geração de IDs", demo_1_generate_ids),
        ("Encoding/Decoding", demo_2_encoding_decoding),
        ("Validação", demo_3_validation),
        ("Normalização", demo_4_normalization),
        ("Extração de UUID", demo_5_uuid_extraction),
        ("Casos Especiais", demo_6_edge_cases),
        ("Performance", demo_7_performance),
    ]

    print("\n\nEscolha uma demonstração:\n")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  0. Executar todas")
    print(f"  q. Sair")

    while True:
        print("\n" + "-" * 70)
        choice = input("\nOpção: ").strip()

        if choice.lower() == "q":
            print("\n👋 Encerrando demonstração.\n")
            break

        if choice == "0":
            for name, demo_func in demos:
                demo_func()
            print("\n\n✅ Todas as demonstrações concluídas!")
            print(
                "\n💡 Execute novamente para ver resultados diferentes (IDs aleatórios)"
            )
            break

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(demos):
                name, demo_func = demos[choice_num - 1]
                demo_func()
            else:
                print(
                    f"❌ Opção inválida. Escolha de 0 a {len(demos)} ou 'q' para sair."
                )
        except ValueError:
            print("❌ Entrada inválida. Digite um número ou 'q'.")


if __name__ == "__main__":
    main()
