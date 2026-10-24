"""Two right-moving waves with adjustable sources and beats.

Start: python gleichlaufende_wellen.py
Dependencies: numpy, matplotlib
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import CheckButtons, Slider, Button

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None

# Lengths are expressed in units of the reference wavelength.
# With f = 0.60 Hz, the wavelength is 1.00 reference units.
SPEED = 0.60
REFERENCE_WAVELENGTH = 1.0
X_MAX = 10.0
INTERVAL_MS = 30
SAMPLE_RATE = 44100
CARRIER_HZ = 400.0
INITIAL_LISTENER_X = 5.0
AUDIO_GAIN = 0.12  # Conservative output level
x = np.linspace(0.0, X_MAX, 2200)
t = 0.0
running = True
audio_stream = None
audio_samples = 0
audio_gain_current = 0.0
audio_enabled = False
audio_params = (1.0, 1.0, 0.60, 0.60, 0.25, 0.25, True, INITIAL_LISTENER_X)

fig, ax = plt.subplots(figsize=(12.8, 7.2))
fig.subplots_adjust(left=0.09, right=0.68, bottom=0.16, top=0.90)
fig.canvas.manager.set_window_title("Gleichlaufende Wellen - Interferenz und Schwebung")

ax.set(xlim=(0, X_MAX), ylim=(-4.2, 4.2),
       xlabel=r"Ort $x/\lambda_0$",
       ylabel="Auslenkung (relative Einheiten)")
ax.set_xticks(np.arange(0.0, X_MAX + 0.01, 1.0))
ax.grid(alpha=0.22)
ax.axhline(0, color="black", lw=0.8, alpha=0.5)
ax.set_title("Zwei getrennte Sender - gleichlaufende Wellen")

line1, = ax.plot([], [], color="#1976d2", lw=1.7, label="Welle 1")
line2, = ax.plot([], [], color="#e59b20", lw=1.7, label="Welle 2")
line_sum, = ax.plot([], [], color="#208c54", lw=2.6, label="Gesamtwelle")
sender1 = ax.axvline(0, color="#1976d2", ls="--", lw=1.1, alpha=0.65)
sender2 = ax.axvline(0.5, color="#e59b20", ls="--", lw=1.1, alpha=0.65)
source1, = ax.plot([0], [0], "o", ms=9, color="#1976d2", zorder=6)
source2, = ax.plot([0.5], [0], "o", ms=9, color="#e59b20", zorder=6)
listener_line = ax.axvline(INITIAL_LISTENER_X, color="#7a3eb1",
                           ls=":", lw=2.0, alpha=0.85)
listener_dot, = ax.plot([INITIAL_LISTENER_X], [0], marker="D",
                        ms=8, color="#7a3eb1", zorder=7, label="Hoerpunkt")
ax.legend(loc="upper left", framealpha=0.92)
info = fig.text(0.09, 0.065, "", fontsize=10)
audio_status = fig.text(0.735, 0.012, "Ton: aus", fontsize=9)

# All controls are placed in a dedicated panel on the right.
# Slider labels are separate from the slider axes to avoid overlap.
PANEL_X = 0.735
SLIDER_X = 0.835
SLIDER_W = 0.115

def section(label, y):
    fig.text(PANEL_X, y, label, fontsize=10, weight="bold")

def make_slider(y, label, minimum, maximum, initial, step):
    fig.text(PANEL_X, y + 0.004, label, fontsize=9, va="center")
    slider_ax = fig.add_axes([SLIDER_X, y, SLIDER_W, 0.023])
    slider = Slider(slider_ax, "", minimum, maximum, valinit=initial,
                    valstep=step, valfmt="%.2f")
    slider.valtext.set_fontsize(9)
    return slider

section("Positionen", 0.915)
listener = make_slider(0.855, r"$x_H/\lambda_0$", 0.0, X_MAX,
                       INITIAL_LISTENER_X, 0.05)
distance = make_slider(0.795, r"$d/\lambda_0$", 0.0, 2.0, 0.25, 0.01)

section("Amplituden", 0.744)
amp1 = make_slider(0.691, r"$A_1$", 0.0, 2.0, 1.0, 0.05)
amp2 = make_slider(0.639, r"$A_2$", 0.0, 2.0, 1.0, 0.05)

section("Frequenzen", 0.588)
freq1 = make_slider(0.535, r"$f_1$ / Hz", 0.20, 1.50, 0.60, 0.01)
freq2 = make_slider(0.483, r"$f_2$ / Hz", 0.20, 1.50, 0.60, 0.01)

section("Anzeige", 0.425)
checks_ax = fig.add_axes([0.74, 0.273, 0.21, 0.130])
checks = CheckButtons(checks_ax, ["Welle 1", "Welle 2", "Gesamtwelle"],
                      [True, True, True])
for label, color in zip(checks.labels, ["#1976d2", "#e59b20", "#208c54"]):
    label.set_color(color)

section("Ton", 0.249)
audio_checkbox_ax = fig.add_axes([0.74, 0.190, 0.18, 0.045])
audio_checkbox = CheckButtons(audio_checkbox_ax, ["Ton an"], [False])
audio_volume_ax = fig.add_axes([SLIDER_X, 0.141, SLIDER_W, 0.023])
fig.text(PANEL_X, 0.145, "Lautst.", fontsize=9, va="center")
audio_volume = Slider(audio_volume_ax, "", 0.0, 1.0,
                      valinit=0.25, valstep=0.01, valfmt="%.2f")
audio_volume.valtext.set_fontsize(9)

pause_ax = fig.add_axes([0.74, 0.058, 0.104, 0.051])
pause_button = Button(pause_ax, "Pause")
reset_ax = fig.add_axes([0.861, 0.058, 0.108, 0.051])
reset_button = Button(reset_ax, "Reset")

def update_curves():
    d = distance.val
    a1, a2 = amp1.val, amp2.val
    f1, f2 = freq1.val, freq2.val
    wavelength1 = SPEED / f1
    wavelength2 = SPEED / f2

    y1 = a1 * np.sin(2 * np.pi * (x / wavelength1 - f1 * t))
    y2_all = a2 * np.sin(2 * np.pi * ((x - d) / wavelength2 - f2 * t))
    right_of_sender2 = x >= d
    y2 = np.where(right_of_sender2, y2_all, np.nan)
    total = np.where(right_of_sender2, y1 + y2_all, np.nan)

    line1.set_data(x, y1)
    line2.set_data(x, y2)
    line_sum.set_data(x, total)
    sender2.set_xdata([d, d])
    x_h = listener.val
    y_h = a1 * np.sin(2 * np.pi * (x_h / wavelength1 - f1 * t))
    if x_h >= d:
        y_h += a2 * np.sin(2 * np.pi * ((x_h - d) / wavelength2 - f2 * t))
    listener_line.set_xdata([x_h, x_h])
    listener_dot.set_data([x_h], [y_h])
    source1.set_data([0], [-a1 * np.sin(2 * np.pi * f1 * t)])
    source2.set_data([d], [-a2 * np.sin(2 * np.pi * f2 * t)])

    global audio_params
    audio_params = (a1, a2, f1, f2, d, audio_volume.val, running, x_h)

    delta_f = abs(f1 - f2)
    if delta_f < 1e-9:
        beat_text = "gleiche Frequenz"
    else:
        beat_text = rf"$f_{{Schwebung}}={delta_f:.2f}$ Hz"
    info.set_text(
        rf"$\lambda_1={wavelength1:.2f}\,\lambda_0$     "
        rf"$\lambda_2={wavelength2:.2f}\,\lambda_0$     "
        rf"$v={SPEED:.2f}\,\lambda_0/s$     "
        + beat_text
    )



def audio_callback(outdata, frames, _time_info, _status):
    """Continuous mono audio: audible carrier plus model frequency offsets."""
    global audio_samples, audio_gain_current
    a1, a2, f1, f2, d, volume, is_running, x_h = audio_params
    seconds = (audio_samples + np.arange(frames)) / SAMPLE_RATE
    audio_samples += frames

    # Audible frequencies are around 400 Hz. Their *difference* is exactly
    # f2-f1; phase differences use the same wavelengths as the plot.
    phase1 = 2 * np.pi * ((CARRIER_HZ + f1 - 0.60) * seconds
                          - f1 * x_h / SPEED)
    phase2 = 2 * np.pi * ((CARRIER_HZ + f2 - 0.60) * seconds
                          - f2 * (x_h - d) / SPEED)
    mixture = a1 * np.sin(phase1)
    if x_h >= d:
        mixture += a2 * np.sin(phase2)
    target_gain = AUDIO_GAIN * volume if is_running else 0.0
    gains = np.linspace(audio_gain_current, target_gain, frames)
    audio_gain_current = target_gain
    outdata[:, 0] = (mixture * gains / 4.0).astype(np.float32)


def toggle_audio(_label):
    global audio_stream, audio_enabled, audio_samples, audio_gain_current
    audio_enabled = bool(audio_checkbox.get_status()[0])
    if audio_enabled:
        if sd is None:
            audio_status.set_text("Ton nicht verfuegbar: sounddevice installieren")
            audio_enabled = False
        else:
            try:
                audio_samples = 0
                audio_gain_current = 0.0
                audio_stream = sd.OutputStream(samplerate=SAMPLE_RATE,
                                               channels=1, dtype="float32",
                                               callback=audio_callback)
                audio_stream.start()
                audio_status.set_text("Ton: an (verschiebbarer Hoerpunkt)")
            except Exception as error:
                if audio_stream is not None:
                    audio_stream.close()
                    audio_stream = None
                audio_enabled = False
                audio_status.set_text("Audiofehler: " + str(error)[:65])
    else:
        if audio_stream is not None:
            audio_stream.stop()
            audio_stream.close()
            audio_stream = None
        audio_status.set_text("Ton: aus")
    if not audio_enabled and audio_checkbox.get_status()[0]:
        audio_checkbox.set_active(0)
    fig.canvas.draw_idle()


def on_close(_event):
    global audio_stream
    if audio_stream is not None:
        audio_stream.stop()
        audio_stream.close()
        audio_stream = None

def toggle_line(label):
    lookup = {"Welle 1": line1, "Welle 2": line2,
              "Gesamtwelle": line_sum}
    artist = lookup[label]
    artist.set_visible(not artist.get_visible())
    fig.canvas.draw_idle()


def toggle_pause(_event):
    global running
    running = not running
    pause_button.label.set_text("Pause" if running else "Start")
    update_curves()
    fig.canvas.draw_idle()


def reset(_event):
    global t, running
    running = True
    t = 0.0
    pause_button.label.set_text("Pause")
    for slider in (listener, distance, amp1, amp2, freq1, freq2, audio_volume):
        slider.reset()
    update_curves()
    fig.canvas.draw_idle()


def on_slider_change(_value):
    update_curves()
    fig.canvas.draw_idle()


def animate(_frame):
    global t
    if running:
        t += INTERVAL_MS / 1000.0
    update_curves()
    return line1, line2, line_sum, source1, source2, sender2, listener_line, listener_dot, info


checks.on_clicked(toggle_line)
audio_checkbox.on_clicked(toggle_audio)
audio_volume.on_changed(on_slider_change)
fig.canvas.mpl_connect("close_event", on_close)
pause_button.on_clicked(toggle_pause)
reset_button.on_clicked(reset)
for slider in (listener, distance, amp1, amp2, freq1, freq2):
    slider.on_changed(on_slider_change)
update_curves()
animation = FuncAnimation(fig, animate, interval=INTERVAL_MS,
                          blit=False, cache_frame_data=False)
plt.show()
