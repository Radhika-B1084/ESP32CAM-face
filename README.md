# Morse Code 
- Open https://wokwi.com/esp32
- Click on the ESP32 Starter Template
- Paste this code
 ```C++
  // Define the pins for the button and LED
  #define BUTTON_PIN 4
  #define LED_PIN 2
  
  // --- Timing Constants ---
  const int TIME_UNIT_MS = 250;
  const int DASH_THRESHOLD_MS = TIME_UNIT_MS;     
  const int LETTER_GAP_MS = TIME_UNIT_MS * 3;     
  const int WORD_GAP_MS = TIME_UNIT_MS * 7;       
  
  // --- Debounce Constants ---
  const unsigned long DEBOUNCE_DELAY_MS = 50; 
  
  // --- Global Variables ---
  String morseBuffer = "";            
  unsigned long pressStart = 0;       
  unsigned long lastRelease = 0;      
  bool buttonState = false;           
  bool lastButtonState = false;       
  bool wordGapAdded = true;           
  unsigned long lastDebounceTime = 0; 
  bool lastFlickerState = false;
  
  // Morse lookup table (unchanged)
  struct MorseMap {
    const char* code;
    char letter;
  };
  
  MorseMap morseTable[] = {
    {".-", 'A'},   {"-...", 'B'}, {"-.-.", 'C'}, {"-..", 'D'},  {".", 'E'},
    {"..-.", 'F'}, {"--.", 'G'},  {"....", 'H'}, {"..", 'I'},  {".---", 'J'},
    {"-.-", 'K'},  {".-..", 'L'}, {"--", 'M'},   {"-.", 'N'},  {"---", 'O'},
    {".--.", 'P'}, {"--.-", 'Q'}, {".-.", 'R'},  {"...", 'S'},  {"-", 'T'},
    {"..-", 'U'},  {"...-", 'V'}, {".--", 'W'},  {"-..-", 'X'}, {"-.--", 'Y'},
    {"--..", 'Z'},
    {"-----", '0'}, {".----", '1'}, {"..---", '2'}, {"...--", '3'},
    {"....-", '4'}, {".....", '5'}, {"-....", '6'}, {"--...", '7'},
    {"---..", '8'}, {"----.", '9'}
  };
  
  char decodeMorse(String code) {
    for (auto &entry : morseTable) {
      if (code.equals(entry.code)) return entry.letter;
    }
    return '?';
  }
  
  void setup() {
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);
    Serial.begin(115200);
    Serial.println("Morse Telegraph Ready! Letters will appear side-by-side.");
    lastFlickerState = (digitalRead(BUTTON_PIN) == LOW);
  }
  
  void loop() {
    unsigned long currentTime = millis();
    bool reading = (digitalRead(BUTTON_PIN) == LOW);
  
    if (reading != lastFlickerState) {
      lastDebounceTime = currentTime;
    }
    lastFlickerState = reading;
  
    if ((currentTime - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
      if (reading != buttonState) {
          buttonState = reading;
  
          if (buttonState) { // Button was just pressed
              pressStart = currentTime;
              digitalWrite(LED_PIN, HIGH);
          } else { // Button was just released
              unsigned long pressDuration = currentTime - pressStart;
              digitalWrite(LED_PIN, LOW);
  
              if (pressDuration < DASH_THRESHOLD_MS) {
                  morseBuffer += ".";
                  // MODIFIED: Removed Serial.print(".");
              } else {
                  morseBuffer += "-";
                  // MODIFIED: Removed Serial.print("-");
              }
              
              lastRelease = currentTime;
              wordGapAdded = false;
          }
      }
    }
  
    // Gap detection logic
    if (!buttonState) {
      unsigned long idleTime = currentTime - lastRelease;
  
      // A letter has just been completed
      if (morseBuffer != "" && idleTime > LETTER_GAP_MS) {
        char decoded = decodeMorse(morseBuffer);
        // MODIFIED: Print the decoded letter directly without a new line
        Serial.print(decoded); 
        morseBuffer = ""; // Clear buffer for the next letter
      }
      
      // A word has just been completed
      if (idleTime > WORD_GAP_MS && !wordGapAdded) {
        // Print a space to separate words
        Serial.print(" "); 
        wordGapAdded = true; 
      }
    }
  }
 ```
- Add a **push button** between any GPIO pin and GND
- Run the code
