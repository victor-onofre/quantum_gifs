"""Render a GIF of an image transformed in Fourier space: QFT^-1 . RZ . RY . QFT on the QPIXL address qubits.

Usage (from the repo root):
    python qft_gif.py my_image.jpg out.gif --max-qubits 7
    python qft_gif.py my_image.jpg test.gif --frames 4
"""

import argparse

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import animation  # noqa: E402
from PIL import Image  # noqa: E402
from qiskit.synthesis import synth_qft_full  # noqa: E402
from qiskit_aer import StatevectorSimulator  # noqa: E402

import QPIXL.helper as hlp  # noqa: E402
from QPIXL.qiskit.qpixl import cFRQI  # noqa: E402

backend = StatevectorSimulator(method="statevector")


def load_channels(path, size):
    img = np.asarray(Image.open(path).convert("RGB").resize((size, size), Image.Resampling.LANCZOS))
    return [img[:, :, c] for c in range(3)]


def qft_transform(qc, k, ang_ry, ang_rz):
    """Apply QFT^-1 . RZ . RY . QFT on the first k address qubits (qubit 0 holds the colour)."""
    if k == 0:
        return qc
    qubits = list(range(1, k + 1))
    qft_k = synth_qft_full(k)
    qc.compose(qft_k, qubits, inplace=True)
    qc.ry(ang_ry, qubits)
    qc.rz(ang_rz, qubits)
    qc.compose(qft_k.inverse(), qubits, inplace=True)
    return qc


def transform_image(chans, k, ang_ry, ang_rz, compress):
    """Encode each RGB channel with cFRQI, apply qft_transform, decode. Returns (rgb image, last circuit)."""
    decoded = []
    for chan in chans:
        tempi = hlp.pad_0(chan.T.flatten())
        qc = qft_transform(cFRQI(tempi, compress), int(k), ang_ry, ang_rz)
        sv = np.real(backend.run(qc).result().get_statevector())
        img = hlp.decodeQPIXL(sv, np.min(tempi), np.max(tempi), scaling=hlp.convertToGrayscaleOld)
        decoded.append(hlp.reconstruct_img(img, chan.shape))
    return np.abs(np.dstack(decoded)).astype(np.uint8), qc


def make_gif(chans, filename, max_qubits, total_frames=240, max_compress=30, fps=25):
    """Sweep k and compress linearly, Ry linearly, Rz as a sine, and save the frames as a GIF."""
    fig = plt.figure(figsize=(14, 14))

    def frame(i):
        t = i / total_frames
        k = round(max_qubits * t)
        ang_ry = 2 * np.pi * t
        ang_rz = 2 * np.pi * (0.5 + 0.5 * np.sin(2 * np.pi * t))
        compress = int(max_compress * t)
        rgb, qc = transform_image(chans, k, ang_ry, ang_rz, compress)
        plt.clf()
        plt.imshow(rgb)
        plt.title(
            f"Frame: {i + 1}/{total_frames}\n"
            f"Width circuit: {qc.width()}\n"
            f"Depth circuit: {qc.depth()}\n"
            f"Num Qubits with QFT: {k}\n"
            f"Ry Angle: {ang_ry:.2f}\n"
            f"Rz Angle: {ang_rz:.2f}\n"
            f"Compress: {compress}"
        )
        print(f"\rframe {i + 1}/{total_frames}", end="", flush=True)

    ani = animation.FuncAnimation(fig, frame, interval=30, frames=total_frames)
    ani.save(filename, writer=animation.PillowWriter(fps=fps))
    plt.close(fig)
    print(f"\nGIF saved to {filename}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image")
    p.add_argument("output")
    p.add_argument("--max-qubits", type=int, default=7)
    p.add_argument("--frames", type=int, default=240)
    p.add_argument("--max-compress", type=int, default=30)
    p.add_argument("--fps", type=int, default=25)
    p.add_argument("--size", type=int, default=82, help="image is resized to size x size")
    a = p.parse_args()

    chans = load_channels(a.image, a.size)
    n_address = int(np.log2(len(hlp.pad_0(chans[0].flatten()))))
    if not 0 <= a.max_qubits <= n_address:
        p.error(f"--max-qubits must be in [0, {n_address}] for a {a.size}x{a.size} image")
    make_gif(chans, a.output, a.max_qubits, a.frames, a.max_compress, a.fps)
