#!/data/data/com.termux/files/usr/bin/bash
# Stay4S Chat Logger v2 - Slaat elke conversatie op als tekstbestand
# Usage: sh /sdcard/Download/stay4s-chat-log.sh [chat|review|list|export]
#
# chat   - Start chatting, alles wordt opgeslagen als .txt
# review - Bekijk gesprekken en markeer goed/slecht voor training
# list   - Toon alle opgeslagen gesprekken
# export - Exporteer alle 'goed' gesprekken voor training
#
# Conversaties worden opgeslagen in /sdcard/Download/stay4s-conversations/
# Elke conversatie is een simpel .txt bestand (kladblok formaat)
#
# Vereist: stay4s-ai.sh start (llama-server op port 8888)

PORT=8888
CHAT_DIR=/sdcard/Download/stay4s-conversations
SYSTEM_PROMPT="Je bent Stay4S AI, een behulpzame Nederlandse klantenservice-assistent. Je antwoordt altijd in het Nederlands, beleefd en duidelijk."

mkdir -p "$CHAT_DIR"

extract_content() {
  grep -o '"content":"[^"]*"' | head -1 | sed 's/"content":"//;s/"$//' | sed 's/\\n/\n/g'
}

chat() {
  if ! curl -s http://127.0.0.1:$PORT/health >/dev/null 2>&1; then
    echo "Server draait niet. Start eerst: sh /sdcard/Download/stay4s-ai.sh start"
    return 1
  fi

  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  DATE=$(date "+%Y-%m-%d %H:%M")
  FILE="$CHAT_DIR/gesprek_$TIMESTAMP.txt"
  
  echo "=== Stay4S Chat ===" > "$FILE"
  echo "Datum: $DATE" >> "$FILE"
  echo "Model: Qwen3-4B-Instruct-2507" >> "$FILE"
  echo "Status: NIET_BEOORDEELD" >> "$FILE"
  echo "================================" >> "$FILE"
  echo "" >> "$FILE"
  
  echo "Stay4S AI Chat - Alles wordt opgeslagen in: $FILE"
  echo "Typ 'stop' om te stoppen | 'goed'/'slecht' om te beoordelen"
  echo "---"
  
  while true; do
    echo -n "Jij: "
    read -r MSG
    
    if [ "$MSG" = "stop" ] || [ "$MSG" = "exit" ]; then
      echo "" >> "$FILE"
      echo "[Einde $(date "+%H:%M:%S")]" >> "$FILE"
      echo "Opgeslagen: $FILE"
      break
    fi
    if [ "$MSG" = "goed" ]; then
      sed -i 's/Status: NIET_BEOORDEELD/Status: GOED_VOOR_TRAINING/' "$FILE"
      echo ">> GOED voor training"
      continue
    fi
    if [ "$MSG" = "slecht" ]; then
      sed -i 's/Status: NIET_BEOORDEELD/Status: SLECHT_VOOR_TRAINING/' "$FILE"
      echo ">> SLECHT voor training"
      continue
    fi
    if [ -z "$MSG" ]; then continue; fi
    
    echo "Jij: $MSG" >> "$FILE"
    RESPONSE=$(curl -s http://127.0.0.1:$PORT/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d "{\"messages\":[{\"role\":\"system\",\"content\":\"$SYSTEM_PROMPT\"},{\"role\":\"user\",\"content\":\"$MSG\"}],\"max_tokens\":250,\"temperature\":0.7}" 2>/dev/null)
    ANSWER=$(echo "$RESPONSE" | extract_content 2>/dev/null)
    if [ -z "$ANSWER" ]; then ANSWER="[Geen antwoord]"; fi
    echo "AI: $ANSWER" >> "$FILE"
    echo "" >> "$FILE"
    echo "AI: $ANSWER"
    echo ""
  done
}

review() {
  echo "=== Gesprek Review ==="
  PENDING=$(grep -l "NIET_BEOORDEELD" "$CHAT_DIR"/gesprek_*.txt 2>/dev/null)
  if [ -z "$PENDING" ]; then
    echo "Geen onbeoordeelde gesprekken."
  else
    for FILE in $PENDING; do
      echo ">>> $(basename $FILE)"
      cat "$FILE"
      echo "----------------------------------------"
      echo -n "Beoordeel: [g]oed / [s]lecht / [o]verslaan: "
      read -r KEUZE
      case "$KEUZE" in
        g|goed) sed -i 's/NIET_BEOORDEELD/GOED_VOOR_TRAINING/' "$FILE"; echo ">> GOED" ;;
        s|slecht) sed -i 's/NIET_BEOORDEELD/SLECHT_VOOR_TRAINING/' "$FILE"; echo ">> SLECHT" ;;
        *) echo ">> Overgeslagen" ;;
      esac
    done
  fi
  GOED=$(grep -l "GOED_VOOR_TRAINING" "$CHAT_DIR"/gesprek_*.txt 2>/dev/null | wc -l)
  SLECHT=$(grep -l "SLECHT_VOOR_TRAINING" "$CHAT_DIR"/gesprek_*.txt 2>/dev/null | wc -l)
  TOTAAL=$(ls "$CHAT_DIR"/gesprek_*.txt 2>/dev/null | wc -l)
  echo "Totaal=$TOTAAL Goed=$GOED Slecht=$SLECHT"
}

list() {
  echo "=== Alle Gesprekken ==="
  for FILE in "$CHAT_DIR"/gesprek_*.txt; do
    [ -f "$FILE" ] || continue
    STATUS=$(grep "Status:" "$FILE" | head -1 | sed 's/Status: //')
    DATUM=$(grep "Datum:" "$FILE" | head -1 | sed 's/Datum: //')
    BERICHTEN=$(grep -c "^Jij:" "$FILE")
    echo "$(basename $FILE) | $DATUM | $STATUS | $BERICHTEN berichten"
  done
}

export_train() {
  GOED_DIR="$CHAT_DIR/training-export"
  mkdir -p "$GOED_DIR"
  COUNT=0
  for FILE in $(grep -l "GOED_VOOR_TRAINING" "$CHAT_DIR"/gesprek_*.txt 2>/dev/null); do
    cp "$FILE" "$GOED_DIR/"
    COUNT=$((COUNT + 1))
  done
  echo "$COUNT gesprekken geexporteerd naar $GOED_DIR/"
}

case "$1" in
  chat)   chat ;;
  review) review ;;
  list)   list ;;
  export) export_train ;;
  *)      echo "Usage: $0 {chat|review|list|export}" ;;
esac