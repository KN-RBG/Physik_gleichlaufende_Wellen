"""Interferenz zweier gleichlaufender Wellen.

Start: python gleichlaufende_wellen.py
Abhaengigkeiten: numpy, matplotlib
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import CheckButtons, Slider, Button

X_MAX = 5.0
AMPLITUDE = 1.0
FREQUENCY = 0.6
FPS_INTERVAL_MS = 30

x = np.linspace(0, X_MAX, 1200)
t = 0.0
running = True

fig, ax = plt.subplots(figsize=(11.5, 6.8))
fig.subplots_adjust(left=0.10, right=0.79, bottom=0.23, top=0.88)
fig.canvas.manager.set_window_title("Gleichlaufende Wellen - Interferenz")

ax.set(xlim=(0, X_MAX), ylim=(-2.3, 2.3),
       xlabel=r"Ort $x/\lambda$", ylabel=r"Auslenkung $y/A$")
ax.set_xticks(np.arange(0, X_MAX + 0.01, 0.5))
ax.grid(alpha=0.23)
ax.axhline(0, color="black", lw=0.8, alpha=0.5)

line1, = ax.plot([], [], color="#1976d2", lw=1.8, label="Welle 1")
line2, = ax.plot([], [], color="#e67e22", lw=1.8, label="Welle 2")
line_sum, = ax.plot([], [], color="#228b54", lw=2.8, label="Ueberlagerung")
ax.legend(loc="upper left", framealpha=0.94)

title = ax.set_title("Interferenz zweier gleichlaufender Wellen")
info = fig.text(0.10, 0.08, "", fontsize=11)

slider_ax = fig.add_axes([0.15, 0.15, 0.57, 0.035])
distance_slider = Slider(slider_ax, r"Abstand $d/\lambda$", 0.0, 2.0,
                         valinit=0.5, valstep=0.01, valfmt="%.2f")

checks_ax = fig.add_axes([0.815, 0.61, 0.175, 0.19])
checks = CheckButtons(checks_ax,
                      ["Welle 1", "Welle 2", "Ueberlagerung"],
                      [True, True, True])
for label, color in zip(checks.labels, ["#1976d2", "#e67e22", "#228b54"]):
    label.set_color(color)

button_ax = fig.add_axes([0.825, 0.47, 0.15, 0.07])
pause_button = Button(button_ax, "Pause")

reset_ax = fig.add_axes([0.825, 0.37, 0.15, 0.07])
reset_button = Button(reset_ax, "Zuruecksetzen")


def update_curves():
    d = distance_slider.val
    phase = 2 * np.pi * (x - FREQUENCY * t)
    wave1 = AMPLITUDE * np.sin(phase)
    wave2 = AMPLITUDE * np.sin(phase - 2 * np.pi * d)
    line1.set_data(x, wave1)
    line2.set_data(x, wave2)
    line_sum.set_data(x, wave1 + wave2)

    max_amp = 2 * AMPLITUDE * abs(np.cos(np.pi * d))
    delta = 360 * d
    info.set_text(
        rf"$d = {d:.2f}\,\lambda$     "
        rf"$\Delta\varphi = {delta:.1f}^\circ$     "
        rf"$A_{{\mathrm{{res}}}} = {max_amp:.2f}\,A$"
    )
    fig.canvas.draw_idle()


def toggle_line(label):
    lookup = {"Welle 1": line1, "Welle 2": line2,
              "Ueberlagerung": line_sum}
    line = lookup[label]
    line.set_visible(not line.get_visible())
    fig.canvas.draw_idle()


def toggle_pause(_event):
    global running
    running = not running
    pause_button.label.set_text("Pause" if running else "Start")
    fig.canvas.draw_idle()


def reset(_event):
    global t, running
    t = 0.0
    running = True
    pause_button.label.set_text("Pause")
    distance_slider.reset()
    update_curves()


def animate(_frame):
    global t
    if running:
        t += FPS_INTERVAL_MS / 1000.0
    update_curves()
    return line1, line2, line_sum


checks.on_clicked(toggle_line)
pause_button.on_clicked(toggle_pause)
reset_button.on_clicked(reset)
distance_slider.on_changed(lambda _value: update_curves())
update_curves()
animation = FuncAnimation(fig, animate, interval=FPS_INTERVAL_MS,
                          blit=False, cache_frame_data=False)
plt.show()
