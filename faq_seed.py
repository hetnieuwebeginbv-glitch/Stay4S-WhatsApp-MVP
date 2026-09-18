"""
FAQ Seed Data -- Test data voor de WhatsApp MVP.
Dit simuleert een MKB-bedrijf (Stay4S als voorbeeldklant).
Mitchell kan later echte klant-FAQ toevoegen via dashboard.
"""
from rag_engine import RAGEngine

SEED_FAQ = [
    {
        "title": "Openingstijden",
        "content": "Stay4S is geopend van maandag tot en met vrijdag, van 9:00 tot 17:00. In het weekend zijn we gesloten. Voor dringende vragen buiten kantooruren kunt u een bericht achterlaten, dan nemen we maandagochtend contact met u op.",
        "source": "FAQ_OPENING.md",
        "doc_type": "faq"
    },
    {
        "title": "Prijzen en pakketten",
        "content": "Stay4S biedt drie pakketten: Basis (EUR 49/maand, 1000 berichten/maand, 1 WhatsApp-nummer), Pro (EUR 99/maand, 5000 berichten, multi-onderwerp, dashboard) en Enterprise (EUR 199/maand, onbeperkt, multi-taal, custom integratie, SLA). Alle pakketten inclusief AI-klantenservice 24/7.",
        "source": "FAQ_PRIJZEN.md",
        "doc_type": "faq"
    },
    {
        "title": "AI Klantenservice",
        "content": "Onze AI-klantenservice draait op StayLM2, een eigen AI-model ontwikkeld door Stay4S. De AI beantwoordt vragen 24/7 in het Nederlands, op basis van uw bedrijfsinformatie. Bij complexe vragen verwijst de AI automatisch door naar een medewerker. De AI leert van elk gesprek om beter te worden.",
        "source": "FAQ_AI.md",
        "doc_type": "faq"
    },
    {
        "title": "Privacy en GDPR",
        "content": "Stay4S neemt privacy serieus. Alle gesprekken worden opgeslagen op eigen infrastructuur in Europa. We delen geen gegevens met Big Tech bedrijven. Klantgegevens worden gehasht opgeslagen. U kunt op elk moment uw gegevens opvragen of verwijderen via privacy@stay4s.com.",
        "source": "FAQ_PRIVACY.md",
        "doc_type": "faq"
    },
    {
        "title": "Doorverwijzing naar medewerker",
        "content": "Als de AI een vraag niet kan beantwoorden of als de klant expliciet om een medewerker vraagt, wordt het gesprek doorgestuurd naar een menselijke medewerker. U krijgt een notificatie en kunt het gesprek overnemen. De AI geeft een samenvatting van het gesprek tot dan toe.",
        "source": "FAQ_DOORVERWIJZING.md",
        "doc_type": "faq"
    },
    {
        "title": "Setup en onboarding",
        "content": "De onboarding duurt ongeveer 1-2 weken. Stap 1: wij koppelen uw WhatsApp-nummer. Stap 2: u levert uw bedrijfsinformatie aan (FAQ, productinfo, tarieven). Stap 3: wij indexeren dit in de AI. Stap 4: u test met 10 gesprekken. Stap 5: livegang na uw goedkeuring.",
        "source": "FAQ_ONBOARDING.md",
        "doc_type": "faq"
    },
    {
        "title": "Stay4S bedrijf informatie",
        "content": "Stay4S is een Nederlands technologiebedrijf opgericht door Mitchell Turk. We bouwen AI-oplossingen voor het MKB: WhatsApp-klantenservice, eigen AI-modellen (StayLM), en telecom-oplossingen. Onze missie: soevereine AI voor Nederlandse bedrijven, zonder Big Tech afhankelijkheid.",
        "source": "FAQ_OVER_ONS.md",
        "doc_type": "faq"
    },
    {
        "title": "Technische ondersteuning",
        "content": "Voor technische problemen kunt u bellen naar 020-1234567 (ma-vr 9:00-17:00) of een e-mail sturen naar support@stay4s.com. Buiten kantooruren beantwoordt de AI algemene vragen. Voor urgente storingen is er een 24/7 noodlijn voor Enterprise-klanten.",
        "source": "FAQ_SUPPORT.md",
        "doc_type": "faq"
    },
    {
        "title": "Opzeggen en garantie",
        "content": "U kunt uw abonnement maandelijks opzeggen zonder opgaaf van reden. Er is geen minimumcontractduur. De eerste maand is gratis als proefperiode. Als u niet tevreden bent, krijgt u uw geld terug, geen vragen gesteld.",
        "source": "FAQ_OPZEGGEN.md",
        "doc_type": "faq"
    },
    {
        "title": "Meertaligheid",
        "content": "De AI-klantenservice spreekt standaard Nederlands. Op verzoek kunnen we Engels, Duits en Frans toevoegen. Voor het Enterprise-pakket is multi-taal standaard inbegrepen. De AI detecteert automatisch de taal van de klant en antwoordt in dezelfde taal.",
        "source": "FAQ_TAAL.md",
        "doc_type": "faq"
    }
]


def seed_faq(db_path: str = None):
    """Vul de database met test-FAQ data."""
    rag = RAGEngine(db_path) if db_path else RAGEngine()
    
    # Check of er al data is
    if rag.count() > 0:
        print(f"Database already has {rag.count()} documents. Skipping seed.")
        return
    
    print(f"Seeding {len(SEED_FAQ)} FAQ documents...")
    for doc in SEED_FAQ:
        rag.add_document(
            title=doc["title"],
            content=doc["content"],
            source=doc["source"],
            doc_type=doc["doc_type"]
        )
    print(f"Done. Database now has {rag.count()} documents.")


if __name__ == "__main__":
    seed_faq()