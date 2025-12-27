# Universal Document Pattern

## Zasada Podstawowa

**WSZYSTKIE dane w systemie UniversalAPI to Documents.**

Nie ma specjalnych tabel dla wyników przetwarzania. Każdy plugin, który przetwarza dokument, tworzy nowy Document jako child (dziecko) dokumentu wejściowego.

## Struktura Document

```
Document
├── id: UUID
├── type_id: FK → document_types.id
├── parent_id: FK → documents.id (NULL dla root documents)
├── owner_id: FK → users.id
├── source_id: FK → sources.id
├── storage_plugin: string (który plugin zarządza plikiem)
├── filepath: string
├── content_type: MIME type
├── size_bytes: int
├── checksum: SHA-256
├── properties: JSONB (wszystkie dane specyficzne dla typu)
└── timestamps
```

## Plugin Output = Child Document

Kiedy plugin przetwarza dokument:

1. Pobiera parent document (input)
2. Wykonuje przetwarzanie
3. **Tworzy nowy Document** z:
   - `parent_id` = ID dokumentu wejściowego
   - `type_id` = typ wyjściowy zarejestrowany przez plugin
   - `owner_id`, `source_id` = kopiowane z parent
   - `properties` = wynik przetwarzania (JSONB)

### Przykład: Audio Transcription

```
audio.mp3 (Document)
├── type: "audio"
├── parent_id: NULL
└── children:
    └── transcription.json (Document)
        ├── type: "transcription"
        ├── parent_id: audio.mp3.id
        └── properties: {
              "full_text": "Transkrypcja...",
              "language": "pl",
              "duration_seconds": 120.5,
              "model_used": "gpt-4o-mini-transcribe"
            }
```

## Wzorcowy kod dla plugin task

```python
async def _process_async(task, document_id, ...):
    from app.core.documents.models import Document, DocumentType

    with get_sync_session() as session:
        # 1. Pobierz parent document
        parent_doc = session.execute(
            select(Document).where(Document.id == UUID(document_id))
        ).scalar_one_or_none()

        # 2. Pobierz output document type
        output_type = session.execute(
            select(DocumentType).where(DocumentType.name == "my_output_type")
        ).scalar_one_or_none()

        # 3. Wykonaj przetwarzanie
        result = await process(...)

        # 4. Przygotuj properties
        properties = {
            "key": "value",
            "data": result.data,
            # ... wszystkie dane wynikowe
        }

        # 5. Utwórz child Document
        child_doc = Document(
            id=uuid4(),
            type_id=output_type.id,
            parent_id=parent_doc.id,
            owner_id=parent_doc.owner_id,
            source_id=parent_doc.source_id,
            storage_plugin="my_plugin",
            filepath=f"{year}/{month}/{day}/{child_id}.json",
            content_type="application/json",
            size_bytes=len(json_bytes),
            checksum=hashlib.sha256(json_bytes).hexdigest(),
            properties=properties,
        )
        session.add(child_doc)
        session.commit()
```

## Properties - co tam wkładać?

Properties (JSONB) zawiera **wszystkie dane specyficzne dla typu dokumentu**:

| Typ | Przykładowe properties |
|-----|------------------------|
| transcription | `{full_text, language, duration_seconds, model_used}` |
| transcription_words | `{full_text, language, words: [{word, start, end, confidence}...]}` |
| analysis | `{summary, entities[], sentiment, keywords[]}` |
| ocr | `{text, pages[], bounding_boxes[]}` |

## Zasada: Jedna Funkcjonalność = Jeden Plugin

**DOBRZE:**
- `audio_transcription` - podstawowa transkrypcja (tylko full_text)
- `audio_transcription_words` - transkrypcja z word-level timestamps

**ŹLE:**
- `audio_transcription` z flagą `word_timestamps: true/false`

Każdy plugin robi jedną rzecz dobrze. Różne warianty = różne pluginy.

## ANTY-WZORCE (NIE RÓB!)

### 1. Osobne tabele dla wyników
```python
# ŹLE - nie rób tego!
class Transcription(Base):
    document_id = ...
    full_text = ...

# DOBRZE - użyj Document
child_doc = Document(
    type_id=transcription_type.id,
    parent_id=audio_doc.id,
    properties={"full_text": ...}
)
```

### 2. Specjalne API endpoints per typ
```python
# ŹLE
@router.get("/transcriptions/{id}")
@router.get("/analyses/{id}")

# DOBRZE - użyj /documents
@router.get("/documents/{id}")  # Uniwersalne!
```

### 3. Dedykowane strony frontend per typ
```tsx
// ŹLE
<Route path="/transcriptions" element={<Transcriptions />} />

// DOBRZE - użyj document detail z type routing
<Route path="/documents/:id" element={<DocumentDetailPage />} />
// FilePreview sprawdza type_name i renderuje odpowiedni komponent
```

### 4. Plugin z wieloma funkcjonalnościami
```python
# ŹLE
settings_schema = {
    "word_timestamps": {"type": "boolean"},  # To powinien być osobny plugin!
}

# DOBRZE - osobne pluginy
class AudioTranscriptionPlugin: ...      # bez words
class AudioTranscriptionWordsPlugin: ... # z words
```

## Frontend - Type Routing

FilePreview automatycznie rozpoznaje typ dokumentu i renderuje odpowiedni komponent:

```tsx
// FilePreview.tsx
const isTranscription = document.type_name === 'transcription'
                     || document.type_name === 'transcription_words'

if (isTranscription) {
  return <TranscriptionPreview document={document} />
}
```

## Related Documents

Child documents są automatycznie widoczne w zakładce "Related" na document detail page:
- Parent → pokazuje swoje children
- Child → pokazuje swojego parent

```tsx
// RelatedDocuments.tsx pokazuje:
// - data.parent (jeśli istnieje)
// - data.children (lista child documents)
```

## Migracja starych danych

Jeśli masz istniejące dane w osobnych tabelach:

1. Utwórz migration z `op.get_bind()` do raw SQL
2. Dla każdego rekordu w starej tabeli:
   - Pobierz parent document info
   - Utwórz child Document z properties
3. Po weryfikacji - usuń stare tabele

Przykład: `alembic/versions/a1b2c3d4e5f6_migrate_transcriptions_to_documents.py`
