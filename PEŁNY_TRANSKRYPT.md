# KOMPLETNY TRANSKRYPT - "90% Win Rate Polymarket Claude ULTRATHINK 5 min Bot (FULL CODE)"
# Moon Dev (Mundavev) - https://youtu.be/85iPljTSSIs
# 20:43 duration, 481 segmentów

## === PELNY TRANSKRYPT (timestampowany) ===

0:00 Wstęp - "All right, I'm trading these five minute markets here on Poly Market..."
0:05 Bot zrobił 50 trade'y wczoraj, stracił 3 (90% win rate)
0:15 Potrzebuje 95% win rate
0:22 BTC up/down 5-minutowe - rotuje co 5 minut
0:30 Pokazał wczoraj kod bota (step 1), dziś step 2
0:45 "jeśli chce zarobić 5% na każdym 5-min rynku, muszę mieć 95% win rate"
1:03 Bot miał 90% WR - ale nie może mieć strat
1:14 "AI to great equalizer"
1:28 Uruchamia Claude Ultra Think
1:40 "przemyśl najlepszy plan"
2:01 Wyjaśnienie tezy - BTC up/down markets
2:32 "uważaj na te up/down markets - jest EFFECTIVE LEVERAGE"
2:43 Wyjaśnienie effective leverage:
   - Nie ma rzeczywistej dźwigni (wkładasz $5)
   - Ale rynki rotują co 5 minut
   - Możesz kupić po 1c i sprzedać po 100c
   - Efektywna dźwignia: 1,000-2,000%
3:35 "oblicz matematykę na tych BTC up/down marketach"
3:49 Analiza Ultra Think: "90% vs 95% to nie problem tuningu - to problem strukturalny"
4:01 "Atakuję to prawdziwymi danymi + wieloma niezależnymi ekspertami + adversarial overfitting checks"
4:27 Wyjaśnienie czym jest Ultra Think (Claude Code)
5:04 Instrukcja instalacji Claude Code
5:30 "Ultra Think wymusza max computational thinking budget 32,000 tokenów"
6:03 "Dosłownie dałem wam kod który wygrywa 90% - to niesamowite"
6:17 Obliczenie effective leverage:
   - BTC ledwo rusza się w 5 minut
   - Mediana ruchu: 6 basis points
   - 45% czasu kończy gdzie zaczęło
   - Entry po 50c = 1,755x leverage
   - Entry po 25c = 5,000x leverage
   - Entry po 10c = 15,000x leverage
   - Entry po 1c = 173,000x leverage!
8:11 "nawet fair 50/50 coin flip przy 1,755x leverage to szaleństwo"
8:33 Workflow running - "ekonomista mapuje dźwignie, quant proponuje fixy"
8:52 "3 niezależne agenty robią Python na 4 latach 1-minutowych danych BTC"
9:00 "backtest 400,000 windows, sprawdza czy 95% WR istnieje"
9:13 "EV każdej alternatywy: niższe ceny bid, kupowanie underdoga, exit scalp"
9:31 "zaczekajmy aż Ultra Think skończy"
10:23 "zrobię 50 pompek"
10:39 "dźwignia tnie w obie strony - house edge jest brutalny"
10:54 "1,755x leverage na ruchu 057 - to wzmocniony coin flip"
11:35 Ultra Think wrócił po 18 minutach:
   - 9 agentów, 3 niezależne backtesty na 400K windows
   - 3 adversarial skeptics
   - **Verdict: DEVASTATING**
11:53 **TEZA: BOT NIE JEST ŹLE DOSTROJONY - JEST PO ZŁEJ STRONIE**
11:56 **OBECNY BOT JEST STRUKTURALNIE NEGATYWNY EV. ZABIJ GO.**
12:01 **FAWORYT (strona która prowadzi w ostatniej minucie) WYGRYWA 87% czasu**
12:07 **nie 95%** - zmierzone na 402,000 windows
12:10 Potwierdzone 87.16% out-of-sample przez 3-cią niezależną replikację
12:23 **Kupowanie faworyta po 95c traci 7.8 centa na kontrakcie strukturalnie**
12:29 Twoje 90% na 28 trade'ach to był szum wokół prawdziwych 87%
12:35 Te 3 straty to nie pech - to strukturalne 13% loss rate
12:40 **Optymalny Kelly = ZERO. Nie uruchamiaj tego ponownie.**
12:50 Jest filtr "cushion/ATR > 2" daje 99% WR - ale sam się unicestwia
13:03 Rynek który wygrywa 99% jest wyceniany na 98-99 centów (nie 95)
13:16 "z twoich 93 prawdziwych filli tylko 6.7% lądowało po 97-95c"
13:34 **FAWORYT: negatywny EV gdy jest do kupienia, niekupowalny gdy +EV**
13:42 **PRAWDZIWA OKAZJA: LUSTRO. KUPUJ TANIO UNDERDOGA.**
13:54 **Underdog wygrywa 33% czasu i jest po płynnej stronie booka**
14:12 "tłum chętnie wyrzuca pewnego przegranego"
14:14 **Skew zmienia się z fatalnego na przyjazny**
14:27 "variancja teraz ci pomaga"
14:36 "ale nie wysyłaj pieniędzy jeszcze"
14:38 Backtest zmierzył win rate underdoga z BTC danych
14:41 zakładał underdog po 5 centów
14:47 **Orderbook catch: underdog może być tani tylko poniżej 20 centów**
14:51 w oknach gdzie wygrywa 1% vs w coin-flip windows gdzie wygrywa 33%
15:00 Book może go wycenić fair na 35-45 centów - brak edge'a
15:10 **DISCIPLINED MOVE: ZBUDUJ SCAN ONLY LOGGER FIRST**
15:18 Każde okno w ostatnich 60 sekundach: zapisz real best ask underdoga
15:25 Uruchom na 1-2 tygodnie - zobaczysz czy underdog jest tani
15:33 Gdy w 33% windows jest tani: buduj tradera z pewnością
15:39 Jeśli nie: uratowałeś bankroll przed mirażem cenowym
15:45 **Teza: ZABIJ FAWORYTA, PRZERZUĆ SIĘ NA UNDERDOGA**
15:53 Buduje scan only logger
16:14 Alternatywny pomysł: szukaj rynków w konsolidacji (rangebound)
16:27 "buduję to dziś"
16:51 "chcę to odpalić LIVE - ale na koncie testowym"
17:24 "zmień na to konto, zbuduj i boom"
18:00 **Kod nazywa się: "five minute dog sniper"**
18:04 "All data dog five minute dog scanner"
18:47 "Python run it"
18:52 Uruchomione - powinno robić trade co kilka minut
19:03 **"Przewijam przez kod żebyście mieli screeny"**
19:12 "Wszystko jest na ekranie. Zrób screena i wrzuć do AI"
19:34 "screenujcie ten kod - wszystko jest tutaj"
19:57 "macie cały kod, widzieliście dużą zmianę"
20:06 Kod dostępny na mundave.com
20:24 **"5 minute 95 cent bid sniper - ten kod jest tutaj"**
20:40 "enjoy it and have beautiful"

## === KLUCZOWE DANE Z WIDEO ===

1. Faworyt wygrywa 87.16% (NIE 95%) - potwierdzone na 402,000 windows
2. Underdog wygrywa ~33% czasu
3. EV kupowania faworyta po 95c = -7.8c/kontrakt
4. EV kupowania underdoga po 5-15c = DODATNIE
5. Effective leverage na 5-min rynkach: 1,755x do 173,000x
6. Kelly dla faworyta = ZERO
7. Strategia: "Scan Only Logger First" przez 1-2 tygodnie
8. Potem: trader na underdoga
