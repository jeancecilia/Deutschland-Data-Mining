"""
Template Engine — defines and renders niche composition templates.

Templates map entity types to candidate phrases.
Example: "{problem} für {audience}" → "Stressbewältigung für Pflegekräfte"
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    name: str
    pattern: str
    required_types: list[str]  # entity types that MUST be present
    optional_types: list[str]  # entity types that CAN be present
    book_type_hint: str | None
    risk_level: str
    priority: int


DEFAULT_TEMPLATES: list[Template] = [
    Template("Problem für Zielgruppe", "{problem} für {audience}", ["problem", "audience"], ["context"], "sachbuch", "low", 95),
    Template("Thema für Zielgruppe", "{topic} für {audience}", ["topic", "audience"], ["context"], "sachbuch", "low", 92),
    Template("Prüfung Lernplaner", "{exam} Lernplaner", ["exam"], ["audience", "profession"], "medium_content", "low", 88),
    Template("Prüfung Prüfungsvorbereitung", "{exam} Prüfungsvorbereitung", ["exam"], ["audience", "profession"], "sachbuch", "low", 86),
    Template("Lebensereignis Checkliste", "{life_event} Checkliste", ["life_event"], ["audience"], "medium_content", "low", 90),
    Template("Lebensereignis Ratgeber", "{life_event} Ratgeber", ["life_event"], ["audience"], "sachbuch", "low", 85),
    Template("Skill für Beruf", "{skill} für {profession}", ["skill", "profession"], ["context"], "sachbuch", "low", 89),
    Template("Thema Workbook", "{topic} Workbook", ["topic"], ["audience", "context"], "sachbuch", "low", 84),
    Template("Thema Arbeitsbuch", "{topic} Arbeitsbuch", ["topic"], ["audience", "context"], "medium_content", "low", 82),
    Template("Objekt Tagebuch", "{object} Tagebuch", ["object"], ["audience", "context"], "medium_content", "low", 84),
    Template("Objekt Logbuch", "{object} Logbuch", ["object"], ["audience", "context"], "medium_content", "low", 78),
    Template("Problem Tagebuch", "{problem} Tagebuch", ["problem"], ["audience", "context"], "medium_content", "medium", 76),
    Template("Problem Workbook für Zielgruppe", "{problem} Workbook für {audience}", ["problem", "audience"], ["context"], "sachbuch", "low", 86),
    Template("Thema Praxisratgeber für Zielgruppe", "{topic} Praxisratgeber für {audience}", ["topic", "audience"], ["context"], "sachbuch", "low", 85),
    Template("Thema Schritt-für-Schritt", "{topic} Schritt-für-Schritt", ["topic"], ["audience"], "sachbuch", "low", 80),
    Template("Thema für Senioren", "{topic} für Senioren", ["topic"], [], "sachbuch", "low", 82),
    Template("Thema für Selbstständige", "{topic} für Selbstständige", ["topic"], [], "sachbuch", "low", 80),
    Template("Thema für Eltern", "{topic} für Eltern", ["topic"], [], "sachbuch", "low", 78),
    Template("Thema für Schüler", "{topic} für Schüler", ["topic"], [], "sachbuch", "low", 76),
    Template("Thema für Anfänger", "{topic} für Anfänger", ["topic"], [], "sachbuch", "low", 88),
    Template("Hobby Trainingsjournal", "{hobby} Trainingsjournal", ["hobby"], ["topic", "audience"], "medium_content", "low", 80),
    Template("Problem Ratgeber", "{problem} Ratgeber", ["problem"], ["audience"], "sachbuch", "medium", 78),
    Template("Beruf Planer", "{profession} Planer", ["profession"], ["audience"], "medium_content", "low", 74),
    Template("Lebensereignis Planer", "{life_event} Planer", ["life_event"], ["audience"], "medium_content", "low", 76),
    Template("Thema + Format", "{topic} {book_format}", ["topic", "book_format"], ["audience"], "medium_content", "low", 90),
    Template("Audience + Thema", "{audience} {topic}", ["audience", "topic"], [], "sachbuch", "low", 72),
    Template("Leben mit Problem", "Leben mit {problem}", ["problem"], ["audience"], "sachbuch", "medium", 74),
    Template("Erfolgreich als Beruf", "Erfolgreich als {profession}", ["profession"], [], "sachbuch", "low", 70),
    Template("Mein Objekt", "Mein {object}", ["object"], ["audience"], "medium_content", "low", 72),
]


class TemplateEngine:
    """Renders templates with entity values."""

    def __init__(self, templates: list[Template] | None = None):
        self._templates: list[Template] = templates or DEFAULT_TEMPLATES

    @property
    def templates(self) -> list[Template]:
        return list(self._templates)

    def render(self, template: Template, values: dict[str, str]) -> str:
        """Replace placeholders in template pattern with actual entity names.

        Example:
            template.pattern = "{problem} für {audience}"
            values = {"problem": "Stressbewältigung", "audience": "Pflegekräfte"}
            → "Stressbewältigung für Pflegekräfte"
        """
        result = template.pattern
        for key, value in values.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, value)
        return result

    def get_template_by_name(self, name: str) -> Template | None:
        for tpl in self._templates:
            if tpl.name == name:
                return tpl
        return None


# Module-level singleton
template_engine = TemplateEngine()
