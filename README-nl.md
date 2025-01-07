# Automatisch K6 Loadtesten met Virtuele Gebruikers

Deze repository bevat twee componenten:
1. **K7 Load Test Automatisering**  
    Dit Python-gebaseerde systeem, genaamd **K7**, automatiseert de uitvoering van K6-scripts. K7 gaat verder dan alleen het opvoeren van de belasting; het bepaalt het **maximaal aantal stabiele virtuele gebruikers (VUs)** dat elke seconde elk eindpunt van een systeem kan bereiken zonder een prestatiecrash te veroorzaken.
2. **K6 Test Script**  
    Een load testing-script voor [K6](https://k6.io/), een open-source tool van Grafana. Het script simuleert meerdere virtuele gebruikers (VUs), verhoogt de belasting geleidelijk en evalueert de systeemprestaties op basis van vooraf gedefinieerde drempelwaarden.

Hoewel K6 de kernfunctionaliteit voor loadtesten biedt, voegt K7 geavanceerde orkestratie en automatisering toe, waardoor het proces efficiënter en nauwkeuriger wordt.

## Inhoudsopgave

1. [Overzicht](#overzicht)  
2. [Test Script](#test-script)  
3. [Authenticatie Instellen (Optioneel)](#authenticatie-instellen-optioneel)  
4. [Drempels en Validatie](#drempels-en-validatie)  
5. [Ondersteunde Eindpunten](#ondersteunde-eindpunten)  
6. [Testcyclus](#testcyclus)  

---

## Overzicht

Het systeem voert K6-loadtesten uit in twee hoofdfasen:
1. **Ramp-Up Fase**: Het aantal virtuele gebruikers wordt geleidelijk verhoogd.
2. **Constante Load Fase**: Een constante belasting van VUs wordt aangehouden.

De testen valideren ook dat de prestatiedrempels worden gehaald en zorgen ervoor dat het systeem de gespecificeerde belasting aankan zonder problemen.

Daarnaast kan het **K7 Python-script** worden gebruikt om testen te beheren en uit te voeren met extra flexibiliteit, inclusief opties voor uitgebreide logging (`-v`/`--verbose`) en hulp (`-h`/`--help`).

---

### Command Line Argumenten

Het script accepteert de volgende opties om de test te configureren:

- **`-h`/`--help`**: Geeft een lijst met alle configuratieopties.
- **`-vu` / `--initial_vus`**: Stel het initiële aantal virtuele gebruikers in. Lagere waarden zijn nuttig wanneer testen direct falen.
- **`-i` / `--increment`**: Stel de verhoging in voor virtuele gebruikers. Kleinere stappen vergroten de nauwkeurigheid, maar duren langer om het stabiele VU-aantal te bepalen. (Aanbevolen: 100)
- **`-vr` / `--validation_runs`**: Stel het aantal validatieruns in. Standaard: 4.
- **`-d` / `--delay_between_tests`**: Stel de vertraging tussen testen in, in seconden. Standaard: 10 seconden.
- **`-t` / `--duration`**: Stel de testduur van K6 in, in seconden. Standaard: 60 seconden.
- **`-rt` / `--rampup_time`**: Stel de ramp-up tijd in, in seconden. Standaard: 15 seconden.
- **`-f` / `--fails`**: Specificeer het aantal keer dat een K6-test mag falen voordat K7 een conclusie trekt. Dit wordt opnieuw ingesteld na elke nieuwe K6-test.
- **`-v` / `--verbose`**: Schakel gedetailleerde output in, inclusief K6-logs.
- **`--k6_script`**: Specificeer het pad naar het K6-testscript. Zie de template voor de structuur.

### Het Script Uitvoeren

Je kunt het script uitvoeren met alle argumenten in één opdracht, zoals hieronder:

```bash
python k7.py -vu 100 -i 50 -vr 5 -d 5 -t 60 -rt 30 -v --k6_script test-script.js
```

Voorbeeldwaarden in deze opdracht:
- 100 initiële virtuele gebruikers (`-vu 100`)
- Verhoging van 50 virtuele gebruikers (`-i 50`)
- 5 validatieruns (`-vr 5`)
- 15 seconden vertraging tussen testen (`-d 5`)
- Testduur van 60 seconden (`-t 60`)
- Ramp-up tijd van 30 seconden (`-rt 30`)
- Gedetailleerde output ingeschakeld (`-v`)
- Gebruik van `test-script.js` als het K6-testscript (`--k6_script test-script.js`).

---

## Test Script

Het hoofdtestscript (`test-script.js`) simuleert virtuele gebruikers (VUs) die HTTP GET-verzoeken uitvoeren. Het is opgebouwd uit twee afzonderlijke loadfasen, waarbij gebruik wordt gemaakt van K6's `ramping-vus` en `constant-vus` executors om de schaalvergroting van VUs te beheren. 

Hier is een voorbeeldscript:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

const target = __ENV.VUS || 300;
const rampupTime = __ENV.RAMPUP || "5s";
const duration = __ENV.DURATION || "1m";

export const options = {
  scenarios: {
    rampUp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [{ duration: rampupTime, target: target }],
      tags: { rampUp: 'true' },
    },
    instantLoad: {
      executor: 'constant-vus',
      vus: target,
      duration: duration,
      startTime: rampupTime,
      tags: { rampUp: 'false' },
    },
  },
  thresholds: {
    'http_req_failed{rampUp:false}': [{ threshold: 'rate==0', abortOnFail: true }],
    'http_req_duration{rampUp:false}': [{ threshold: 'p(95)<1000', abortOnFail: true }],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(90)', 'p(95)'],
};

export default function () {
  http.get('http://localhost:3000/channel');
  http.get('http://localhost:3000/channel/create');
  sleep(1);
}
```

---

## Authenticatie Instellen (Optioneel)

Als je test JWT-authenticatie vereist, kun je de loginflow instellen als volgt:

```javascript
export function setup() {
  const loginHeaders = { 'Content-Type': 'application/json' };

  const loginResponse = http.post('http://localhost/auth/login', JSON.stringify({
    name: 'je_gebruikersnaam',
    password: 'je_wachtwoord',
  }), { headers: loginHeaders });

  const isLoginSuccessful = check(loginResponse, {
    'login successful': (res) => res.status === 200 && res.json('accessToken') !== undefined,
  });

  if (!isLoginSuccessful) {
    throw new Error('Login failed');
  }

  return loginResponse.json('accessToken');
}

export default function (accessToken) {
  const authHeaders = { Authorization: `Bearer ${accessToken}` };

  http.get('http://localhost:3000/channel', { headers: authHeaders });
  http.get('http://localhost:3000/channel/create', { headers: authHeaders });
  sleep(1);
}
```

---

## Drempels en Validatie

De volgende prestatiedrempels zijn gedefinieerd voor validatie:
- **HTTP-verzoeksfouten**: Het foutpercentage moet 0% zijn (`rate==0`).
- **HTTP-verzoekstijd**: 95% van de verzoeken moet binnen 1000ms voltooid zijn (`p(95)<1000`).

---

## Ondersteunde Eindpunten

Alle HTTP-methoden worden ondersteund in K6, behalve `trace`. Raadpleeg de [K6-documentatie](https://k6.io/) voor meer informatie.

---

## Testcyclus

K7 volgt een gestructureerde aanpak om het maximale stabiele aantal virtuele gebruikers (VUs) voor je systeem te bepalen:

1. **Incrementele Load Testing**  
2. **Hervalmechanisme bij Fouten**  
3. **Verfijning van VU-aantal**  
4. **Validatieruns**  
5. **Eindresultaten**  
6. **Foutafhandeling**

Zie de Engelse uitleg voor meer details.
