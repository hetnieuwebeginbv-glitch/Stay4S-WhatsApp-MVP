"""
Stay4Safe AI -- Phishing & Scam Detector.
Analyseert doorgestuurde berichten op phishing/scam indicators.
Draait op Pi 5, gebruikt Ollama + RAG met scam knowledge base.
"""
import os
import re
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")
logger = logging.getLogger("stay4s.safe")

# Scam indicators (Nederlandse context)
SCAM_INDICATORS = {
    "urgency": {
        "patterns": ["dringend", "onmiddellijk", "nu", "vandaag nog", "laatste kans", "spoed",
                     "uw account wordt geblokkeerd", "24 uur", "48 uur", "actie vereist"],
        "weight": 15,
        "description": "Vals gevoel van urgentie"
    },
    "money_request": {
        "patterns": ["overboeking", "betaal", "bedrag", "euro", "EUR", "overmaken",
                     "iDEAL", "creditcard", "pincode", "rekeningnummer", "IBAN",
                     "crypto", "bitcoin", "giftcard", "voucher", "pakbon"],
        "weight": 20,
        "description": "Vraag om geld of betaalgegevens"
    },
    "personal_info": {
        "patterns": ["wachtwoord", "inloggen", "gebruikersnaam", "BSN", "paspoort",
                     "rijbewijs", "persoonsgegevens", "verificatie", "bevestig uw",
                     "voer uw in", "geef uw", "DigiD", "voornaam", "achternaam",
                     "geboortedatum", "adres"],
        "weight": 20,
        "description": "Vraag om persoonlijke gegevens"
    },
    "impersonation": {
        "patterns": ["Belastingdienst", "CBP", "Politie", "KvK", "gemeente",
                     "bank", "ING", "Rabobank", "ABN AMRO", "SNS", "Postbus",
                     "Apple", "Google", "Microsoft", "Netflix", "bol.com",
                     "DHL", "PostNL", "UPS", "FedEx", "overboeking onbekende"],
        "weight": 15,
        "description": "Imitatie van bekende organisatie"
    },
    "suspicious_links": {
        "patterns": ["http://", "https://", "klik hier", "volg link", "bezoek website",
                     "controleer uw", "verifieer", ".tk", ".ml", ".ga", ".cf",
                     "bit.ly", "tinyurl", "shortener", "login-", "verify-",
                     "account-", "secure-", "update-"],
        "weight": 15,
        "description": "Verdachte links of verkorte URLs"
    },
    "too_good": {
        "patterns": ["gewonnen", "prijs", "loterij", "gratis", "korting",
                     "100% gratis", "geen kosten", "rijk", "geld verdienen",
                     "investering", "rendement", "garantie", "bonus"],
        "weight": 10,
        "description": "Te goed om waar te zijn"
    },
    "threats": {
        "patterns": ["boete", "straf", "vervolging", "gerechtelijk",
                     "haal utrecht", "incasso", "deurwaarder", "blokkering",
                     "uitschrijving", "schuld", "openstaande"],
        "weight": 15,
        "description": "Dreigementen met consequenties"
    },
    "language_anomalies": {
        "patterns": ["Beste klant", "Beste gebruiker", "Geachte heer/mevrouw",
                     "translation", "automatisch vertaald", "fouten",
                     "ongebruikelijke formulering"],
        "weight": 5,
        "description": "Onnatuurlijke of vertaalde taal"
    },
    "phone_packages": {
        "patterns": ["pakket afgeleverd", "bezorgpoging", "pakket staat klaar",
                     "ophalen bij", "douane", "invoerrechten", "verzendkosten",
                     "pakketnummer", "track and trace", "volg uw pakket"],
        "weight": 12,
        "description": "Nep pakketbezorging scam"
    },
    "subscription_trap": {
        "patterns": ["abonnement", "opzeggen", "verlenging", "automatische verlenging",
                     "kosten worden afgeschreven", "bedrag wordt ingenomen",
                     "stopzetten", "annuleren"],
        "weight": 10,
        "description": "Nep abonnement/abonnement-val"
    }
}


def analyze_message(text: str) -> dict:
    """
    Analyseer bericht op scam/phishing indicators.
    Geeft risk score (0-100), categorieen, en advies.
    """
    text_lower = text.lower()
    findings = []
    total_score = 0
    categories = []

    for category, info in SCAM_INDICATORS.items():
        matches = []
        for pattern in info["patterns"]:
            if pattern.lower() in text_lower:
                matches.append(pattern)

        if matches:
            score = min(info["weight"], info["weight"])
            total_score += score
            categories.append({
                "category": category,
                "description": info["description"],
                "weight": info["weight"],
                "matched_patterns": matches[:3],  # max 3 voor rapport
                "score": score
            })
            findings.append(f"- {info['description']} (gewicht: {info['weight']})")

    # Extra heuristiek
    # URL analyse
    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', text)
    suspicious_urls = []
    for url in urls:
        suspicious = False
        if any(tld in url.lower() for tld in [".tk", ".ml", ".ga", ".cf", ".gq"]):
            suspicious = True
        if "bit.ly" in url or "tinyurl" in url or "t.co" in url:
            suspicious = True
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):  # IP address
            suspicious = True
        if len(url) > 60:
            suspicious = True
        if suspicious:
            suspicious_urls.append(url)
            total_score += 10

    # Telefoonnummer analyse
    phone_patterns = re.findall(r'(?:\+31|0|0031)[\s-]?\d[\s-]?\d{8}', text)
    if phone_patterns:
        total_score += 5
        findings.append("- Telefoonnummer in bericht (risico indicator)")

    # Cap score
    risk_score = min(total_score, 100)

    # Bepaal risico niveau
    if risk_score >= 60:
        risk_level = "HOOG"
        advice = "WAARSCHUWING: Dit bericht is zeer waarschijnlijk een scam/phishing poging. "
        advice += "Niet op links klikken, geen gegevens delen, geen geld overmaken. "
        advice += "Verwijder het bericht en blokkeer de afzender."
        is_scam = True
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        advice = "LET OP: Dit bericht bevat verdachte elementen. "
        advice += "Wees voorzichtig. Controleer de afzender via officiële kanalen. "
        advice += "Niet op verdachte links klikken."
        is_scam = False
    else:
        risk_level = "LAAG"
        advice = "Dit bericht lijkt veilig. Geen duidelijke scam indicatoren gevonden. "
        advice += "Blijf echter altijd alert op onverwachte berichten."
        is_scam = False

    # Bouw rapport
    report = f"=== STAY4SAFE AI ANALYSE ===\n\n"
    report += f"Risico score: {risk_score}/100 ({risk_level})\n\n"

    if findings:
        report += "Gevonden indicatoren:\n"
        report += "\n".join(findings) + "\n\n"

    if suspicious_urls:
        report += f"Verdachte links gevonden: {len(suspicious_urls)}\n"
        for url in suspicious_urls[:3]:
            report += f"  - {url[:80]}\n"
        report += "\n"

    if phone_patterns:
        report += f"Telefoonnummer(s) in bericht: {len(phone_patterns)}\n\n"

    report += f"ADVIES: {advice}\n\n"
    report += f"Analyse door Stay4Safe AI --Privacy-first, lokaal op eigen infra.\n"
    report += f"Tijd: {datetime.now().strftime('%d-%m-%Y %H:%M')}"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "is_scam": is_scam,
        "categories": categories,
        "suspicious_urls": suspicious_urls,
        "phone_numbers": phone_patterns,
        "findings": findings,
        "advice": advice,
        "report": report,
        "timestamp": datetime.now().isoformat()
    }