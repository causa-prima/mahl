# Mahl - Dokumentation

Dieser Ordner enthält die vollständige Projekt-Dokumentation für die "Mahl"-App.

---

## Übersicht der Dokumente

### Für LLM-Implementierung (START HERE!)

| Dokument | Zweck | Zielgruppe |
|----------|-------|------------|
| **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** | 📋 **Zentrale technische Spezifikation** - Architektur, Tech-Stack, Patterns, Phasen | LLM für Implementierung, Entwickler |
| **[LLM_PROMPT_TEMPLATE.md](LLM_PROMPT_TEMPLATE.md)** | 🤖 Fertige Prompts zum Copy-Paste für LLMs | Product Owner, Entwickler |
| **[AGENT_MEMORY.md](AGENT_MEMORY.md)** | 🧠 Session-übergreifendes Gedächtnis des implementierenden Agenten | LLM (Primär), Entwickler (Review) |

### Fachliche Spezifikation

| Dokument | Zweck | Zielgruppe |
|----------|-------|------------|
| **[GLOSSARY.md](GLOSSARY.md)** | 📖 **Ubiquitäre Sprache** - Domain-Modell, Fachbegriffe (bindend!) | Alle (LLM, Entwickler, PO) |
| **[USER_STORIES.md](USER_STORIES.md)** | 📝 **Alle Features** mit Szenarien, Akzeptanzkriterien und Prioritäten | LLM, Product Owner, Tester |

---

## Dokumenten-Hierarchie

```
Start
  ↓
[IMPLEMENTATION_GUIDE.md] ← Zentrale Spezifikation
  ├─→ [GLOSSARY.md] ← Domain-Begriffe
  ├─→ [USER_STORIES.md] ← Feature-Details
  └─→ [LLM_PROMPT_TEMPLATE.md] ← Prompt-Vorlagen
```

---

## Schnellstart für LLMs

Wenn du ein LLM bist und dieses Projekt implementieren sollst:

1. ✅ Prüfe **AGENT_MEMORY.md** - Wurde bereits an dem Projekt gearbeitet?
2. ✅ Lies **IMPLEMENTATION_GUIDE.md** vollständig
3. ✅ Lies **GLOSSARY.md** für Domain-Begriffe
4. ✅ Lies **USER_STORIES.md** für Feature-Details
5. ✅ Lies **../CLAUDE.md** für Code-Patterns
6. ✅ Analysiere bestehenden Code in `Shared/`, `Server/`
7. ✅ Beginne mit SKELETON-Phase (falls nicht bereits abgeschlossen)
8. ✅ **TDD:** Tests ZUERST schreiben!
9. ✅ **Sub-Agenten konsultieren:** Refactoring, UI/UX, Security
10. ✅ **AGENT_MEMORY.md aktualisieren** am Ende jeder Session
11. ✅ Bei Fragen: Frage den Product Owner!

---

## Schnellstart für Entwickler

Wenn du ein menschlicher Entwickler bist:

1. Lies **IMPLEMENTATION_GUIDE.md** für technischen Überblick
2. Konsultiere **GLOSSARY.md** bei Fachbegriffen
3. Verwende **LLM_PROMPT_TEMPLATE.md** zum Arbeiten mit LLMs
4. Siehe **../CLAUDE.md** für Build-Commands und Patterns

---

## Änderungshistorie

| Datum | Version | Änderung |
|-------|---------|----------|
| 2026-02-17 | 1.0 | Initiale Dokumentation erstellt |

---

## Hinweise

- **Bindende Dokumente:** GLOSSARY.md (Domain-Begriffe) und IMPLEMENTATION_GUIDE.md (Architektur-Patterns)
- **Living Documents:** USER_STORIES.md wird evtl. erweitert/angepasst
- **Nicht in Git:** Konfigurationsdateien mit Secrets (`.env`, `appsettings.Production.json`)

Bei Fragen oder Unklarheiten: GitHub Issues erstellen oder direkt im Team besprechen.
