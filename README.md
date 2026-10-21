# Gleichlaufende Wellen - Interferenz und Schwebungen

Python-Simulation zweier gleichlaufender, raeumlich getrennter Wellenquellen.

## Start

```bash
pip install -r requirements.txt
python gleichlaufende_wellen.py
```

## Bedienung

- Abstand d: 0 bis 2 Referenzwellenlaengen (lambda_0).
- A1, A2: Amplituden der Sender unabhaengig von 0 bis 2.
- f1, f2: Frequenzen der Sender unabhaengig von 0.20 bis 1.50 Hz.
- Die Wellenlaengen lambda_1 und lambda_2 werden aus v/f berechnet und angezeigt.
- Checkboxen zum Ein-/Ausblenden beider Einzelwellen und der Gesamtwelle.
- Pause/Start und Reset.

## Physikalisches Modell

Beide Sender strahlen nach rechts ab. Sender 1 steht bei x=0, Sender 2 bei x=d.
Die Gesamtwelle erscheint erst rechts von Sender 2 (x>=d); links davon sieht
man nur Welle 1. Die farbigen Senderpunkte schwingen jeweils mit ihrer eigenen
Amplitude und Frequenz.

Es gilt eine gemeinsame, konstante Phasengeschwindigkeit v=0.60 lambda_0/s.
Dadurch aendern sich bei Anpassung der Frequenz auch die Wellenlaengen:
lambda_i=v/f_i. Beim Ausgangswert f1=f2=0.60 Hz gilt lambda_1=lambda_2=lambda_0.

y1(x,t) = A1 sin(2 pi (x/lambda_1 - f1*t))
y2(x,t) = A2 sin(2 pi ((x-d)/lambda_2 - f2*t)), nur fuer x>=d
y_gesamt(x,t) = y1(x,t) + y2(x,t), nur fuer x>=d

Bei kleinen Frequenzunterschieden und aehnlichen Amplituden laesst sich eine
Schwebung beobachten: f_Schwebung=|f1-f2|. Zum Beispiel f1=0.60 Hz,
f2=0.70 Hz, A1=A2=1.0; die Schwebungsperiode betraegt dann 10 s.

Die Simulation stellt den eingeschwungenen Zustand dar, nicht die Wellenfront
beim erstmaligen Einschalten der Quellen. Alle Langen sind auf lambda_0 bezogen.
