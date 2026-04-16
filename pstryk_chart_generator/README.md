# Pstryk Chart Generator Add-on

Ten dodatek cyklicznie generuje wysoce zoptymalizowane obrazy z wykresami zużycia energii w powiązaniu z tanimi i drogimi strefami, wyciągając dane historyczne za ostatnie 14 dni by nakreślić wyprzedzającą mapę trendu dla wykresu obrazkowego.

## Informacje o katalogu
Wygenerowane pliki ładują się do folderu widocznego dla Frontendów:
`/config/www/pstryk_chart_generator/chart_pstryk.png`
`/config/www/pstryk_chart_generator/chart_pstryk_yesterday.png`

## Konfiguracja Ręcznego Wywołania ("Na Żądanie")
Rozwiązanie zoptymalizowane; zamiast stałych obciążających pętli (pooling), instalacja tego widoku posiłkuje się natywną dla HA systemową integracją serwisów (**Actions**) w sposób bezpośrdni łącząc przycisk z serwerem uśpionym w Add-onie (obsługiwanym bezszelestnie przez Aiohttp).

1. Przejdź w Home Assistant do edycji systemowego pliku `configuration.yaml`
2. Wklej nową definicję `rest_command` (Akcję HTTP), aby uderzyć w Webhook tego Add-ona po udostępnionym porcie (8099):

```yaml
rest_command:
  generate_pstryk_chart:
    url: "http://core-pstryk-chart-generator:8099/generate"
    method: GET
```

*(Uwaga: adres bazuje na formacie nazwy hosta systemowego: skrót twojego slug i dodana koncówka, powszechnie `core-` oraz zamienione podkresiiki. Ewentualnie gdyby logi w HA odrzuciły "hostname not found" zastosuj po prostu przydzielony z routera docelowy IP pod ten kontener).*

3. Zrestartuj Home Assistanta lub przeładuj konfigurację YAML (Narzędzia Deweloperskie -> Akcje -> `homeassistant.reload_all`).
4. Gotowe! Stworzyliśmy nowy, poprawny serwis systemowy: `Action: rest_command.generate_pstryk_chart`. Możesz przypiąć go do dowolnej encji typu karta "Button" ze zwyczajnym poleceniem by wykonał tę akcję po naciśnięciu.
