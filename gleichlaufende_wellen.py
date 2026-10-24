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
LISTENER_X = 5.0
AUDIO_GAIN = 0.12  # Conservative output level
x = np.linspace(0.0, X_MAX, 2200)
t = 0.0
running = True
audio_stream = None
audio_samples = 0
audio_gain_current = 0.0
audio_enabled = False
audio_params = (1.0, 1.0, 0.60, 0.60, 0.5, 0.25, True)

fig, ax = plt.subplots(figsize=(13.8, 7.4))
fig.subplots_adjust(left=0.08, right=0.69, bottom=0.14, top=0.91)
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
ax.legend(loc="upper left", framealpha=0.92)
info = fig.text(0.08, 0.035, "", fontsize=10)
audio_status = fig.text(0.74, 0.015, "Ton: aus", fontsize=9)

def make_slider(y, label, minimum, maximum, initial, step):
    slider_ax = fig.add_axes([0.785, y, 0.16, 0.030])
    return Slider(slider_ax, label, minimum, maximum, valinit=initial,
                  valstep=step, valfmt="%.2f")

distance = make_slider(0.79, r"$d/\lambda_0$", 0.0, 2.0, 0.50, 0.01)
amp1 = make_slider(0.68, r"$A_1$", 0.0, 2.0, 1.0, 0.05)
amp2 = make_slider(0.60, r"$A_2$", 0.0, 2.0, 1.0, 0.05)
freq1 = make_slider(0.47, r"$f_1$ / Hz", 0.20, 1.50, 0.60, 0.01)
freq2 = make_slider(0.39, r"$f_2$ / Hz", 0.20, 1.50, 0.60, 0.01)

checks_ax = fig.add_axes([0.755, 0.19, 0.22, 0.16])
checks = CheckButtons(checks_ax, ["Welle 1", "Welle 2", "Gesamtwelle"],
                      [True, True, True])
for label, color in zip(checks.labels, ["#1976d2", "#e59b20", "#208c54"]):
    label.set_color(color)

audio_checkbox_ax = fig.add_axes([0.76, 0.125, 0.11, 0.046])
audio_checkbox = CheckButtons(audio_checkbox_ax, ["Ton an"], [False])
audio_volume_ax = fig.add_axes([0.895, 0.146, 0.076, 0.02])
audio_volume = Slider(audio_volume_ax, "Lautst.", 0.0, 1.0,
                      valinit=0.25, valstep=0.01, valfmt="%.2f")

pause_ax = fig.add_axes([0.74, 0.07, 0.105, 0.055])
pause_button = Button(pause_ax, "Pause")
reset_ax = fig.add_axes([0.865, 0.07, 0.115, 0.055])
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
    source1.set_data([0], [-a1 * np.sin(2 * np.pi * f1 * t)])
    source2.set_data([d], [-a2 * np.sin(2 * np.pi * f2 * t)])

    global audio_params
    audio_params = (a1, a2, f1, f2, d, audio_volume.val, running)

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
    a1, a2, f1, f2, d, volume, is_running = audio_params
    seconds = (audio_samples + np.arange(frames)) / SAMPLE_RATE
    audio_samples += frames

    # Audible frequencies are around 400 Hz. Their *difference* is exactly
    # f2-f1; phase differences use the same wavelengths as the plot.
    phase1 = 2 * np.pi * ((CARRIER_HZ + f1 - 0.60) * seconds
                          - f1 * LISTENER_X / SPEED)
    phase2 = 2 * np.pi * ((CARRIER_HZ + f2 - 0.60) * seconds
                          - f2 * (LISTENER_X - d) / SPEED)
    mixture = a1 * np.sin(phase1) + a2 * np.sin(phase2)
    target_gain = AUDIO_GAIN * volume if is_running else 0.0
    gains = np.linspace(audio_gain_current, target_gain, frames)
    audio_gain_current = target_gain
    outdata[:, 0] = (mixture * gains / 4.0).astype(np.float32)


def toggle_audio(_label):
    global audio_stream, audio_enabled, audio_samples, audio_gain_current
    audio_enabled = not audio_enabled
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
                audio_status.set_text("Ton: an (Hoerpunkt x=5)")
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
    for slider in (distance, amp1, amp2, freq1, freq2, audio_volume):
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
    return line1, line2, line_sum, source1, source2, sender2, info


checks.on_clicked(toggle_line)
audio_checkbox.on_clicked(toggle_audio)
audio_volume.on_changed(on_slider_change)
fig.canvas.mpl_connect("close_event", on_close)
pause_button.on_clicked(toggle_pause)
reset_button.on_clicked(reset)
for slider in (distance, amp1, amp2, freq1, freq2):
    slider.on_changed(on_slider_change)
update_curves()
animation = FuncAnimation(fig, animate, interval=INTERVAL_MS,
                          blit=False, cache_frame_data=False)
plt.show()
