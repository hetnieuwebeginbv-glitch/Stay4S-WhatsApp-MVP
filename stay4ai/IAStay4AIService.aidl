// IAStay4AIService.aidl — de Stay4OS-AI-systeemservice
// Elke Stay4OS-app kan de AI aanroepen via deze interface.
package com.stay4s.ai;

interface IAStay4AIService {
    // Chat met het eigen model (lokaal of via Pi 5/serverless)
    String chat(String prompt, int maxTokens);

    // Vat tekst samen
    String summarize(String text);

    // Veiligheidscheck (scam/phishing detectie)
    String detectScam(String text);

    // Start een agent-taak (agent-factory)
    String runAgent(String task);

    // Status van het AI-model (loaded, modelnaam, snelheid)
    String getStatus();
}