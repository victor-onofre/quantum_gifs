# Images vs QFT

Animated GIFs of an image being rotated in Fourier space on a quantum computer (simulated).

Each RGB channel of the image is encoded into a quantum state with QPIXL (FRQI). A rotation is applied in Fourier space on the first `k` address qubits, and the state is decoded back into an image:

$$ QFT_{1,k}^{-1}\, RZ_{1,k}(\theta_z)\, RY_{1,k}(\theta_y)\, QFT_{1,k}\, |\text{Image}\rangle $$

Qubit 0 holds the colour and qubits 1..n the pixel address. An 82×82 image is padded to 2¹³ pixels, so it uses 13 address qubits plus 1 colour qubit. With `k = 0`, or both angles at 0, you get the original image back.

## Install

Python 3.12:

```bash
pip install -r requirements.txt
```

or with conda / [Miniforge](https://github.com/conda-forge/miniforge):

```bash
conda create -n qft-gifs python=3.12
conda activate qft-gifs
pip install -r requirements.txt
```

## Usage

Run from the repo root:

```bash
python qft_gif.py my_image.jpg out.gif --max-qubits 7
python qft_gif.py my_image.jpg test.gif --frames 4   # quick test
```

Any RGB image works; it is resized to `--size`×`--size`.

| Option | Default | Meaning |
|---|---|---|
| `--max-qubits` | 7 | largest `k`; at most 13 for 82×82 |
| `--frames` | 240 | number of frames |
| `--max-compress` | 30 | final QPIXL compression (% of smallest angles dropped) |
| `--fps` | 25 | GIF frame rate |
| `--size` | 82 | image side in pixels |

Across the frames (t from 0 to 1):

- `k` goes from 0 to `max_qubits`, stepwise.
- θ_y goes from 0 to 2π, linearly.
- θ_z = 2π·(0.5 + 0.5·sin(2πt)).
- `compress` goes from 0 to `max_compress`, linearly.

Each frame runs three statevector simulations, one per colour channel, so the full 240 frames take a while.

## Credits

The `QPIXL/` folder is copied from [QuantumArtHack](https://github.com/victor-onofre/QuantumArtHack), which is based on [HeidelbergQuantum/ParallelQPIXL](https://github.com/HeidelbergQuantum/ParallelQPIXL) by Daniel Bultrini.
QPIXL algorithm: Amankwah et al., *Quantum pixel representations and compression for N-dimensional images*, Sci. Rep. 12, 7712 (2022), https://doi.org/10.1038/s41598-022-11024-y.
