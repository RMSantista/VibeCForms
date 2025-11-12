# Tags as State Implementation Plan (Revised)

## Overview
Implement VibeCForms Convention #4: "Tags as State" with Crockford Base32 UUIDs, tag storage/API for both TXT and SQLite backends, and hybrid configuration approach.

### VibeCForms Crockford Variation
This implementation uses a **modified Crockford Base32** encoding:
- **Standard Crockford**: Uses modulo 37 with check symbols `*~$=U` (5 special characters for values 32-36)
- **VibeCForms Variation**: Uses modulo 32 with check digit from the same 32-character alphabet
- **Rationale**:
  - All IDs are fully URL-safe (no reserved characters)
  - Consistent character set throughout entire ID
  - Simpler implementation (no special symbol mapping)
  - Still provides error detection capability (1 in 32 chance of random error passing)
- **Trade-off**: Slightly reduced error detection (32 vs 37 possible check values), but sufficient for our use case

## Phase 1: Migrate to Crockford Base32 UUIDs

### Important: Crockford Base32 Format (VibeCForms Variation)
- **Character set**: `0123456789ABCDEFGHJKMNPQRSTVWXYZ` (32 symbols, excludes I, L, O, U)
- **UUID encoding**: 128 bits → 26 Base32 characters (⌈128 ÷ 5⌉ = 25.6 → 26)
- **Check digit**: Uses modulo 32 (instead of 37), mapped to same 32-symbol character set
  - **VibeCForms variation**: Check digit uses `0123456789ABCDEFGHJKMNPQRSTVWXYZ`
  - **Standard Crockford**: Uses `*~$=U` for values 32-36
  - **Benefit**: All characters are URL-safe, consistent, and easy to type
- **Final format**: 27 characters total (26 encoded + 1 check digit)
- **Example**: `3HNMQR8PJSG0C9VWBYTE12K` where `K` is the check digit
- **URL Safety**: ✅ All characters are RFC 3986 unreserved or safe for URLs

### 1.1 Implement Crockford Base32 Encoder
- Create `src/utils/crockford.py` utility module
- Implement UUID → Crockford Base32 encoding (uppercase)
- Add check digit calculation and validation (using modulo 32)
- Example output: `3HNMQR8PJSG0C9VWBYTE12K` (27 chars: 26 for UUID + 1 check digit)
- Check digit uses same character set: `0123456789ABCDEFGHJKMNPQRSTVWXYZ`
- **IMPORTANT**: Always store the full 27-character ID including check digit
- **Algorithm**:
  1. Generate UUID v4 (128 bits)
  2. Encode to Base32 (26 characters)
  3. Calculate checksum: Convert 26-char string to integer, modulo 32
  4. Map checksum (0-31) to character set
  5. Append check digit as 27th character
- Use standard UUID v4 for generation, encode for display/storage
- Note: 128-bit UUID encodes to exactly 26 Base32 digits (⌈128/5⌉ = 26)

### 1.2 Update BaseRepository Interface
- Add `id` field (Crockford Base32 string) to all record operations
- Replace index-based methods completely:
  - `create()` - now returns generated ID
  - `read_by_id(form_path, spec, id)` - replaces `read_one(idx)`
  - `update_by_id(form_path, spec, id, data)` - replaces `update(idx, data)`
  - `delete_by_id(form_path, spec, id)` - replaces `delete(idx)`
- Add `id_exists(form_path, id)` - check if ID exists

### 1.3 Update TxtRepository
- New file format: `ID;field1;field2;...` (ID with check digit in first column)
- Generate Crockford Base32 ID for new records (27 chars including check digit)
- Store complete ID including check digit in TXT files
- Implement ID-based lookup (scan file for matching ID)
- Remove all index-based methods
- Create migration utility: `scripts/migrate_txt_to_ids.py`

### 1.4 Update SQLiteRepository
- Add `id VARCHAR(27) PRIMARY KEY` column (stores Crockford Base32 with check digit)
- Remove auto-increment integer IDs completely
- Generate Crockford Base32 ID in `create()`
- Update all queries to use `id` column
- Create migration: `scripts/migrate_sqlite_to_ids.py`

### 1.5 Update Application Layer
- Replace all route parameters: `/<form>/edit/<id>`, `/<form>/delete/<id>`
- Update `VibeCForms.py` to use ID-based repository methods
- Remove all index-based logic (no backward compatibility needed)
- Display full IDs (with check digit) in tables (copyable, monospace font)
- Add ID validation in routes:
  - Verify Crockford format (27 chars, valid character set)
  - Validate check digit before any operation
  - Reject IDs with invalid checksums

### 1.6 Update Templates
- Modify `form.html`: show ID column, use IDs in edit/delete links
- Modify `edit.html`: display record ID at top
- Add CSS for ID display (monospace, easy to select/copy)
- Remove all index references

### 1.7 Data Migration
- Create backup of current data
- Run migration scripts for all existing forms
- Generate Crockford Base32 IDs for all existing records
- Verify migration success (record count, data integrity)
- Update schema_history.json

### 1.8 Update Tests
- Replace all index-based test assertions with ID-based
- Add tests for Crockford encoding/decoding
- Test ID validation and checksum verification
- Test ID uniqueness and generation
- Remove backward compatibility tests

## Phase 2: Implement Tag Storage

### 2.1 Define Tag Data Structure
- Schema: `{object_type, object_id (Crockford), tag, applied_at, applied_by, metadata}`
- Support multiple tags per object
- Track tag history (who applied, when)
- Store object_id as Crockford Base32 string

### 2.2 Extend BaseRepository for Tags
- Add abstract methods:
  - `add_tag(form_path, object_id, tag, applied_by, metadata=None)`
  - `remove_tag(form_path, object_id, tag)`
  - `get_tags(form_path, object_id)` → list of tag dicts
  - `has_tag(form_path, object_id, tag)` → boolean
  - `get_objects_by_tag(form_path, tag)` → list of object IDs
  - `remove_all_tags(form_path, object_id)`
  - `replace_tag(form_path, object_id, old_tag, new_tag)` - for state transitions

### 2.3 Implement TxtRepository Tags
- Create `<form>_tags.txt` files (one per form)
- Format: `object_id;tag;applied_at;applied_by;metadata_json`
- Object IDs stored as Crockford Base32
- Implement all tag methods with file operations
- Handle concurrent access safely

### 2.4 Implement SQLiteRepository Tags
- Create global `tags` table: `id, object_type, object_id, tag, applied_at, applied_by, metadata`
- `object_id` column stores Crockford Base32 string
- Add indexes: `idx_object_id`, `idx_tag`, `idx_object_type_tag`
- Implement all tag methods with SQL
- Use transactions for atomic tag operations

### 2.5 Tag Configuration Schema
- Form spec: `"tags": {"enabled": true, "allow_multiple": true, "predefined_tags": ["lead", "qualified"]}`
- Global config in persistence.json: `"tags": {"enabled_by_default": true, "storage_mode": "dedicated"}`
- Hybrid logic: global default + per-form override

## Phase 3: Tag API & Service Layer

### 3.1 Create TagService
- File: `src/services/tag_service.py`
- Business logic for tag operations
- Validate Crockford IDs before tag operations
- Check if tags enabled for form (read config)
- Validate tags against predefined list (if configured)

### 3.2 Core Tag Operations
- `add_tag(form_path, record_id, tag, applied_by)` - Add single tag, validate ID
- `remove_tag(form_path, record_id, tag)` - Remove single tag
- `has_tag(form_path, record_id, tag)` - Check tag exists
- `get_tags(form_path, record_id)` - Get all tags for record (with metadata)
- `get_objects_by_tag(form_path, tag)` - Find all records with tag
- `transition_state(form_path, record_id, from_tag, to_tag, applied_by)` - State transition

### 3.3 API Endpoints
- `POST /api/<form>/tags/<id>` - Add tag (body: `{"tag": "qualified", "applied_by": "user"}`)
- `DELETE /api/<form>/tags/<id>/<tag>` - Remove tag
- `GET /api/<form>/tags/<id>` - Get all tags for record
- `GET /api/<form>/objects-by-tag/<tag>` - Get records with tag (returns IDs + basic info)
- `PUT /api/<form>/tags/<id>/transition` - State transition (body: `{"from": "lead", "to": "qualified"}`)

### 3.4 Integration with Routes
- Add tag display in record views (badges/chips)
- Allow adding/removing tags when creating/editing records
- Show tags column in table (optional, configurable)
- Add tag filter dropdown in form view

## Phase 4: Testing & Documentation

### 4.1 Crockford ID Tests
- Test UUID → Crockford encoding/decoding
- Test check digit calculation and validation (modulo 32)
- Test that check digit uses only valid Base32 characters
- Test ID uniqueness across records
- Test invalid ID rejection (wrong length, invalid chars, bad checksum)
- Test case-insensitive decoding (lowercase input accepted, stored as uppercase)

### 4.2 Tag Operation Tests
- Test add/remove/has/get tags with Crockford IDs
- Test multiple tags per object
- Test get_objects_by_tag
- Test tag persistence across app restarts
- Test state transitions

### 4.3 Backend Tests
- Test tag operations in TxtRepository
- Test tag operations in SQLiteRepository
- Test backend migration with tags (TXT → SQLite)
- Verify tags preserved during migration

### 4.4 Configuration Tests
- Test global tag enable/disable
- Test per-form tag override
- Test predefined tags validation
- Test hybrid configuration logic

### 4.5 Documentation Updates
- Update README.md with tag examples and Crockford ID info
- Update ARCHITECTURE.md with ID system and tag design
- Update TECH_DEBT.md to mark Convention #4 complete
- Create `docs/tags_guide.md` with usage examples
- Create `docs/crockford_ids.md` explaining ID format

## Deliverables

1. **Crockford Base32 ID System**: All records use human-friendly, typeable IDs with checksums
2. **Tag Storage**: Tags stored in both TXT and SQLite backends
3. **Tag API**: Complete REST API for tag operations
4. **Tag Service**: Business logic layer for tag management
5. **Configuration**: Hybrid approach (global + per-form override)
6. **Tests**: Comprehensive test coverage (aim for 25+ new tests)
7. **Documentation**: Complete guides for IDs and tags
8. **Migration**: Scripts to migrate existing data to new system

## Files to Create
- `src/utils/crockford.py` - Crockford Base32 encoder/decoder (VibeCForms variation)
  - Functions: `encode_uuid()`, `decode()`, `validate()`, `generate_id()`
  - Uses modulo 32 for check digit (not standard modulo 37)
  - All characters from same 32-symbol set
- `src/services/tag_service.py` - Tag business logic
- `tests/test_crockford.py` - Crockford encoding tests
- `tests/test_tags.py` - Tag operation tests
- `tests/test_tag_migration.py` - Tag migration tests
- `docs/tags_guide.md` - User guide for tags
- `docs/crockford_ids.md` - Explanation of ID format and VibeCForms variation
- `scripts/migrate_txt_to_ids.py` - TXT data migration
- `scripts/migrate_sqlite_to_ids.py` - SQLite data migration

## Files to Modify
- `src/persistence/base.py` - Replace index methods with ID methods, add tag methods
- `src/persistence/adapters/txt_adapter.py` - Implement ID + tag support
- `src/persistence/adapters/sqlite_adapter.py` - Implement ID + tag support
- `src/VibeCForms.py` - Replace all index logic with ID logic, add tag routes
- `src/templates/form.html` - Display IDs and tags
- `src/templates/edit.html` - Display IDs and tag management
- `src/config/persistence.json` - Add tag configuration
- All test files - Update for ID-based operations

## Success Criteria
✅ All records have Crockford Base32 IDs (uppercase, with checksum)
✅ IDs are human-readable and typeable
✅ Can add/remove/query tags on any record
✅ Tags persist across application restarts
✅ Tags migrate correctly between backends
✅ Configuration works (global + per-form override)
✅ API endpoints functional and tested
✅ All existing tests pass with new ID system
✅ Documentation complete and accurate
✅ No backward compatibility code
