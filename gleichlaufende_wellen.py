"""Two right-moving waves with adjustable sources and beats.

Start: python gleichlaufende_wellen.py
Dependencies: numpy, matplotlib
"""
import time
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
clock_anchor = time.perf_counter()
clock_elapsed = 0.0
audio_stream = None
audio_gain_current = 0.0
audio_sample_count = 0
audio_enabled = False
audio_params = (1.0, 1.0, 0.60, 0.60, 0.25, 0.25, True, INITIAL_LISTENER_X)

fig, ax = plt.subplots(figsize=(12.8, 7.2))
fig.subplots_adjust(left=0.08, right=0.66, bottom=0.43, top=0.91)
phasor_ax = fig.add_axes([0.72, 0.43, 0.25, 0.48])
phasor_ax.set(xlim=(-4.2,4.2), ylim=(-4.2,4.2), title="Zeigerdiagramm am Hörpunkt")
phasor_ax.set_aspect("equal", adjustable="box")
phasor_ax.grid(alpha=0.22)
phasor_ax.axhline(0, color="gray", lw=0.8)
phasor_ax.axvline(0, color="gray", lw=0.8)
phasors = [phasor_ax.quiver([0],[0],[0],[0], angles="xy", scale_units="xy", scale=1, color=color, width=0.012) for color in ("#1976d2","#e59b20","#208c54")]
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
info = fig.text(0.08, 0.365, "", fontsize=10)
audio_status = fig.text(0.72, 0.015, "Ton: aus", fontsize=9)

# Settings below both diagrams.
def make_slider(x0, y, label, minimum, maximum, initial, step):
    fig.text(x0, y + 0.012, label, fontsize=9, va="center")
    slider = Slider(fig.add_axes([x0+0.105, y, 0.15, 0.025]), "", minimum, maximum,
                    valinit=initial, valstep=step, valfmt="%.2f")
    slider.valtext.set_fontsize(9)
    return slider

fig.text(0.08, 0.31, "Positionen", weight="bold")
listener = make_slider(0.08, 0.25, r"$x_H/\lambda_0$", 0, X_MAX, INITIAL_LISTENER_X, 0.05)
distance = make_slider(0.08, 0.19, r"$\delta/\lambda_0$", 0, 3, 0.25, 0.01)
fig.text(0.08, 0.15, "Gangunterschied", fontsize=9)
fig.text(0.40, 0.31, "Amplituden und Frequenzen", weight="bold")
amp1 = make_slider(0.40, 0.25, r"$A_1$", 0, 2, 1, 0.05)
amp2 = make_slider(0.40, 0.19, r"$A_2$", 0, 2, 1, 0.05)
freq1 = make_slider(0.40, 0.13, r"$f_1$ / Hz", 0.20, 1.50, 0.60, 0.01)
freq2 = make_slider(0.40, 0.07, r"$f_2$ / Hz", 0.20, 1.50, 0.60, 0.01)
checks = CheckButtons(fig.add_axes([0.72, 0.20, 0.24, 0.13]), ["Welle 1", "Welle 2", "Gesamtwelle"], [True, True, True])
for label, color in zip(checks.labels, ["#1976d2", "#e59b20", "#208c54"]):
    label.set_color(color)
audio_checkbox = CheckButtons(fig.add_axes([0.72, 0.15, 0.24, 0.045]), ["Ton an"], [False])
audio_volume = make_slider(0.72, 0.10, "Lautst.", 0, 1, 0.25, 0.01)
pause_button = Button(fig.add_axes([0.72, 0.045, 0.11, 0.04]), "Pause")
reset_button = Button(fig.add_axes([0.85, 0.045, 0.11, 0.04]), "Reset")

def model_time(now=None):
    """Monotonic shared time for plot and audio; freezes while paused."""
    if now is None:
        now = time.perf_counter()
    return clock_elapsed + (now - clock_anchor if running else 0.0)


def update_curves():
    global t
    t = model_time()
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
    z1 = a1 * np.exp(2j * np.pi * (x_h / wavelength1 - f1 * t))
    z2 = a2 * np.exp(2j * np.pi * ((x_h - d) / wavelength2 - f2 * t)) if x_h >= d else 0j
    for arrow, z, visible in zip(phasors, (z1, z2, z1+z2), checks.get_status()):
        arrow.set_UVC([z.real], [z.imag])
        arrow.set_visible(visible)
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
    """Audio carrier with exactly the same low-frequency phase as the plot.

    The instantaneous interference envelope matches the plotted model at
    the selected listener point; the 400-Hz carrier is an audible proxy.
    """
    global audio_gain_current, audio_sample_count
    a1, a2, f1, f2, d, volume, is_running, x_h = audio_params
    start = model_time()
    offsets = np.arange(frames) / SAMPLE_RATE
    seconds = start + offsets

    # Same spatial and slow temporal phase as the visible two waves.
    model_phase1 = 2 * np.pi * (f1 * x_h / SPEED - f1 * seconds)
    model_phase2 = 2 * np.pi * (f2 * (x_h - d) / SPEED - f2 * seconds)
    # The audible carrier MUST use consecutive sample indices. Deriving it
    # from perf_counter at each callback caused clicks and a buzzing tone.
    carrier = 2 * np.pi * CARRIER_HZ * (audio_sample_count + np.arange(frames)) / SAMPLE_RATE
    audio_sample_count += frames
    mixture = a1 * np.sin(carrier + model_phase1)
    if x_h >= d:
        mixture += a2 * np.sin(carrier + model_phase2)

    target_gain = AUDIO_GAIN * volume if is_running else 0.0
    gains = np.linspace(audio_gain_current, target_gain, frames)
    audio_gain_current = target_gain
    outdata[:, 0] = (mixture * gains / 4.0).astype(np.float32)


def toggle_audio(_label):
    global audio_stream, audio_enabled, audio_gain_current, audio_sample_count
    audio_enabled = bool(audio_checkbox.get_status()[0])
    if audio_enabled:
        if sd is None:
            audio_status.set_text("Ton nicht verfuegbar: sounddevice installieren")
            audio_enabled = False
        else:
            try:
                audio_gain_current = 0.0
                audio_sample_count = 0
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
    update_curves()
    fig.canvas.draw_idle()


def toggle_pause(_event):
    global running, clock_elapsed, clock_anchor
    now = time.perf_counter()
    clock_elapsed = model_time(now)
    running = not running
    clock_anchor = now
    pause_button.label.set_text("Pause" if running else "Start")
    update_curves()
    fig.canvas.draw_idle()


def reset(_event):
    global t, running, clock_anchor, clock_elapsed
    running = True
    t = 0.0
    clock_elapsed = 0.0
    clock_anchor = time.perf_counter()
    pause_button.label.set_text("Pause")
    for slider in (listener, distance, amp1, amp2, freq1, freq2, audio_volume):
        slider.reset()
    update_curves()
    fig.canvas.draw_idle()


def on_slider_change(_value):
    update_curves()
    fig.canvas.draw_idle()


def animate(_frame):
    update_curves()
    return line1, line2, line_sum, source1, source2, sender2, listener_line, listener_dot, info


# Feine Zwischenwerte bleiben verfuegbar. Beim Loslassen des
# Abstandreglers rasten benachbarte Halb-Wellenlaengen-Werte exakt ein.
distance_dragging = False


def distance_press(event):
    global distance_dragging
    distance_dragging = (event.inaxes is distance.ax)


def distance_release(_event):
    global distance_dragging
    if not distance_dragging:
        return
    distance_dragging = False
    nearest = round(distance.val * 2.0) / 2.0
    if abs(distance.val - nearest) <= 0.03:
        distance.set_val(nearest)


fig.canvas.mpl_connect("button_press_event", distance_press)
fig.canvas.mpl_connect("button_release_event", distance_release)

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
