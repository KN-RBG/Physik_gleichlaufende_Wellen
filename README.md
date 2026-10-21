# Gleichlaufende Wellen - Interferenz

Python-Animation zur Interferenz zweier gleichlaufender Wellen gleicher Frequenz und Amplitude.

## Start

```bash
pip install -r requirements.txt
python gleichlaufende_wellen.py
```

## Bedienung

- **Abstand d/lambda:** Regler von 0 bis 2 Wellenlaengen.
- **Welle 1 / Welle 2 / Ueberlagerung:** Ein- und ausblendbar.
- **Pause / Start:** Animation anhalten oder fortsetzen.
- **Zuruecksetzen:** Abstand auf 0.5 lambda und Zeit auf 0 setzen.

## Modell

Beide Erreger schwingen gleichphasig. Der Abstand d wird als Laufwegunterschied und damit als Phasenverschiebung modelliert:

```text
y1(x,t) = A sin(2 pi (x/lambda - f t))
y2(x,t) = A sin(2 pi (x/lambda - f t - d/lambda))
yres = y1 + y2

Delta phi = 2 pi d/lambda
Ares = 2 A |cos(pi d/lambda)|
```

Die Darstellung zeigt die Wellen in einem gemeinsamen Beobachtungsbereich mit
einer durch den Erregerabstand bestimmten Phasenverschiebung. Der Raum
zwischen den Erregern und das Einsetzen der Wellen an ihrem jeweiligen Erreger
werden nicht gesondert modelliert.

Konstruktive Interferenz: d = 0, 1, 2 lambda.
Destruktive Interferenz: d = 0.5, 1.5 lambda.
