# Gleichlaufende Wellen - Interferenz und Schwebungen

Python-Simulation zweier gleichlaufender, raeumlich getrennter Wellenquellen.

## Start

```bash
pip install -r requirements.txt
python gleichlaufende_wellen.py
```

## Bedienung

- Hoerpunkt x_H: 0 bis 10 Referenzwellenlaengen, mit violetter Linie und Punkt.
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

## Audio (optional)

Mit der Checkbox "Ton an" laesst sich eine akustische Gesamtwelle einschalten.
Die Lautstaerke kann ueber den separaten Regler eingestellt werden. Zuerst
mit niedriger Lautstaerke testen.

Installation: `pip install sounddevice` (auch in requirements.txt enthalten).
Die Audio-Ausgabe benoetigt ein funktionierendes Audio-Ausgabegeraet.

Die Audiofrequenzen liegen bei 400 Hz + (f_i - 0.60 Hz). Dadurch stimmt die
Frequenzdifferenz, also die Schwebungsfrequenz, exakt mit der Simulation
ueberein, waehrend ein gut hoerbarer Grundton erhalten bleibt. Der Ton
repraesentiert das Signal am einstellbaren Hoerpunkt x_H. Links von Sender 2
ist nur der erste Sender hoerbar; ab dem zweiten Sender die Ueberlagerung.
Die Phasenverschiebung der beiden Sender entspricht dort dem Wellenbild.
Die Tonhoehe ist also bewusst in den hoerbaren Bereich verschoben; die
gezeichneten Wellen selbst bleiben niederfrequente Modellwellen.
Pause schaltet den Ton stumm; Start setzt ihn fort. Das Audio ist nicht
samplegenau mit der Bildschirmanimation synchronisiert.

## Synchronisation von Bild und Ton

Grafik und Audio verwenden dieselbe monotone Modellzeit (mit Pause und Reset).
Die phasenbestimmenden Terme fuer die beiden Wellen sind in beiden Ausgaben
identisch. Fuer den Ton wird eine schnelle 400-Hz-Traegerschwingung addiert;
der frequenzabhaengige Interferenzverlauf und die Schwebungshuellen stimmen
mit dem Modell am beweglichen Hoerpunkt ueberein.

Die schnelle 400-Hz-Traegerschwingung selbst ist nicht als sichtbare Schwingung
im Diagramm dargestellt. Treiber- und Audiopufferlatenz koennen zu kleinen
zeitlichen Verzoegerungen fuehren; es ist keine samplegenaue Bild/Ton-Synchronisation.
