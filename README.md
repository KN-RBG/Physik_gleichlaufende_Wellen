# Gleichlaufende Wellen - Interferenz

Python-Animation zur Interferenz zweier gleichlaufender Wellen gleicher Frequenz und Amplitude.

## Start

```bash
pip install -r requirements.txt
python gleichlaufende_wellen.py
```

## Bedienung

- **Abstand d/lambda:** Regler von 0 bis 2 Wellenlaengen.
- **Welle 1 / Welle 2 / Gesamtwelle:** Ein- und ausblendbar.
- **Pause / Start:** Animation anhalten oder fortsetzen.
- **Zuruecksetzen:** Abstand auf 0.5 lambda und Zeit auf 0 setzen.

## Modell

Beide Erreger schwingen gleichphasig. Der Abstand d wird als Laufwegunterschied und damit als Phasenverschiebung modelliert:

```text
y1(x,t) = A sin(2 pi (x/lambda - f t))
y2(x,t) = A sin(2 pi (x/lambda - f t - d/lambda))   nur fuer x >= d
yres = y1                                           fuer x < d
yres = y1 + y2                                      fuer x >= d

Delta phi = 2 pi d/lambda
Ares = 2 A |cos(pi d/lambda)|
```

Sender 1 steht bei x=0, Sender 2 bei x=d. Beide senden gleichphasig nach rechts.
Von x=0 bis x=d ist nur Welle 1 sichtbar. Ab x=d wird Welle 2 hinzuaddiert.
Die gruen dargestellte Gesamtwelle ist daher vor dem zweiten Sender mit Welle 1 identisch.
Die Formel fuer die resultierende Amplitude gilt nur im gemeinsamen Ausbreitungsbereich x>=d.
Gezeigt wird der eingeschwungene Zustand, keine Einschaltfront.

Konstruktive Interferenz: d = 0, 1, 2 lambda.
Destruktive Interferenz: d = 0.5, 1.5 lambda.
