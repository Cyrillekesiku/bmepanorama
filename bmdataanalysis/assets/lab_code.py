# Biomedical Data Analysis lab: all code cells in order.
# Works in VS Code / Spyder (cells are separated by '# %%') or paste into Jupyter.

# %% [01-neurons-to-numbers]
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Schematic electrode positions: (angle from the nose in degrees, radius), 10-20 flat map.
# Order = order of the 14 EEG columns in the CSV file.
POLAR = {"af3": (-30, .43), "f7": (-54, .511), "f3": (-40, .30), "fc5": (-69, .38),
         "t7": (-90, .511), "p7": (-126, .511), "o1": (-162, .511), "o2": (162, .511),
         "p8": (126, .511), "t8": (90, .511), "fc6": (69, .38), "f4": (40, .30),
         "f8": (54, .511), "af4": (30, .43)}
CH = list(POLAR)                      # ['af3', 'f7', 'f3', ...]
POS = {ch: (r * np.sin(np.deg2rad(a)) / .511, r * np.cos(np.deg2rad(a)) / .511)
       for ch, (a, r) in POLAR.items()}          # x to the right, y toward the nose

REGION = {"af3": "Frontal", "af4": "Frontal", "f3": "Frontal", "f4": "Frontal", "f7": "Frontal", "f8": "Frontal",
          "fc5": "Frontal", "fc6": "Frontal", "t7": "Temporal", "t8": "Temporal",
          "p7": "Parietal", "p8": "Parietal", "o1": "Occipital", "o2": "Occipital"}
COLORS = {"Frontal": "#1f62b8", "Temporal": "#2f9e44", "Parietal": "#e8590c", "Occipital": "#7048e8"}

def draw_head(ax, r=1.12):
    """Head outline (circle, nose, ears) in the same units as POS."""
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(r * np.cos(t), r * np.sin(t), "k", lw=1.5)
    ax.plot([-.14, 0, .14], [r - .01, r + .14, r - .01], "k", lw=1.5)                 # nose
    for s in (-1, 1):                                                             # ears
        ax.plot(s * (r + np.array([0, .06, .08, .06, 0])), np.array([.18, .14, 0, -.14, -.18]), "k", lw=1.5)
    ax.set_xlim(-1.35, 1.35); ax.set_ylim(-1.3, 1.4); ax.set_aspect("equal"); ax.axis("off")

fig, ax = plt.subplots(figsize=(5.2, 5.2))
draw_head(ax)
for ch, (x, y) in POS.items():
    ax.scatter(x, y, s=470, color=COLORS[REGION[ch]], edgecolor="k", zorder=3)
    ax.text(x, y, ch.upper(), ha="center", va="center", color="w", fontsize=8.5, weight="bold", zorder=4)
for reg, col in COLORS.items():
    ax.scatter([], [], s=90, color=col, label=reg)
ax.legend(loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(.5, -.06), fontsize=8)
ax.set_title("EPOC X channels (view from above, nose up)")
plt.show()

# %% [02-dataset]
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal, stats

# A clean, consistent plotting style for the whole lab
plt.rcParams.update({"figure.figsize": (10, 3.2), "axes.grid": True, "grid.alpha": .25,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 10, "axes.titleweight": "bold", "lines.linewidth": 1.0})

CSV = "SE1_EPOCX_213291_20240304_140920.csv"    # <- path to the recording
df = pd.read_csv(CSV)

print("shape (rows, columns):", df.shape)
print(f"memory in RAM: {df.memory_usage().sum() / 1e6:.0f} MB")
print("data types:", df.dtypes.value_counts().to_dict())

# %% [02-dataset]
df.iloc[:5, :10]

# %% [02-dataset]
prefix = pd.Series(df.columns).str.split(".").str[0]
prefix = prefix.where(prefix.isin(["eeg", "cq", "mot", "sq"]), "bookkeeping")
print(prefix.value_counts().to_string())

# %% [02-dataset]
FS = 128                                              # nominal EEG sampling rate (Hz), verified in Section 3
streams = {"eeg.af3": "EEG", "cq.af3": "contact quality", "mot.accx": "motion",
           "sq.af3.rms": "sensor quality"}
rate = pd.DataFrame({"stream": streams.values(),
                     "fraction of rows filled": [df[col].notna().mean() for col in streams]},
                    index=list(streams))
rate["rate (Hz)"] = rate["fraction of rows filled"] * FS
rate

# %% [02-dataset]
cols = ["eeg.af3", "cq.af3", "mot.accx", "sq.af3.rms"]
mask = df.loc[:139, cols].notna().to_numpy().T            # 4 streams x 140 rows

fig, ax = plt.subplots(figsize=(10, 2.2))
ax.imshow(mask, aspect="auto", cmap="Blues", interpolation="nearest")
ax.set_yticks(range(4)); ax.set_yticklabels(cols)
ax.set_xlabel("row number"); ax.set_title("Which cells contain a value? (dark = filled, white = empty)")
ax.grid(False)
plt.show()

# %% [02-dataset]
eeg_cols = [f"eeg.{ch}" for ch in CH]
check = df[eeg_cols].describe(percentiles=[.01, .99]).T[["mean", "std", "min", "1%", "99%", "max"]]
check.index = CH
check.round(1)

# %% [03-time-axis]
t = df["timestamp"].to_numpy() - df["timestamp"].iloc[0]     # seconds since the first sample
dt = np.diff(t)                                               # spacing between rows

print(f"first sample : {pd.to_datetime(df['timestamp'].iloc[0], unit='s')} UTC")
print(f"last sample  : {pd.to_datetime(df['timestamp'].iloc[-1], unit='s')} UTC")
print(f"duration     : {t[-1]:.2f} s = {t[-1] / 60:.2f} min")
print(f"number of samples N = {len(t)}")
print(f"median spacing = {np.median(dt) * 1e3:.4f} ms  ->  fs = {1 / np.median(dt):.3f} Hz")
print(f"mean rate (N-1)/duration = {(len(t) - 1) / t[-1]:.3f} Hz")
print(f"smallest / largest spacing: {dt.min() * 1e3:.4f} / {dt.max() * 1e3:.4f} ms")

# %% [03-time-axis]
fig, ax = plt.subplots(1, 2, figsize=(10, 3.3))

ax[0].hist(dt * 1e3, bins=np.linspace(7.806, 7.8135, 60), color="#1f62b8")
ax[0].axvline(1000 / FS, color="crimson", ls="--", label="nominal 1000/128 = 7.8125 ms")
ax[0].set_xlabel("spacing between consecutive rows (ms)"); ax[0].set_ylabel("count")
ax[0].set_title("Sampling interval"); ax[0].legend(fontsize=8)

drift = (df["originaltimestamp"] - df["timestamp"]).to_numpy() * 1e3          # milliseconds
ax[1].plot(t / 60, drift, color="#e8590c")
ax[1].set_xlabel("time (min)"); ax[1].set_ylabel("originaltimestamp − timestamp (ms)")
ax[1].set_title("Slow drift between the two clocks")
plt.tight_layout(); plt.show()

# %% [03-time-axis]
step = np.diff(df["eeg.counter"].to_numpy()) % 128            # difference modulo 128 (wrap-around)
print("counter increments :", pd.Series(step).value_counts().to_dict())
print("interpolated flags :", df["eeg.interpolated"].value_counts().to_dict())
print("index increments   :", pd.Series(np.diff(df["index"])).value_counts().to_dict())

# %% [03-time-axis]
def seg(ch, t0, t1):
    """Return (time in s, voltage in µV) of channel `ch` between t0 and t1 seconds."""
    n0, n1 = int(t0 * FS), int(t1 * FS)
    return np.arange(n0, n1) / FS, df[f"eeg.{ch}"].to_numpy()[n0:n1]

fig, ax = plt.subplots(3, 1, figsize=(10, 7))
x_all = df["eeg.o1"].to_numpy()
ax[0].plot(np.arange(len(x_all)) / FS / 60, x_all, lw=.3)
ax[0].set_xlabel("time (min)"); ax[0].set_title("O1, the whole recording (26 min)")

ts, xs = seg("o1", 600, 610)
ax[1].plot(ts, xs); ax[1].set_xlabel("time (s)"); ax[1].set_title("O1, a 10-second window")

ts, xs = seg("o1", 600, 601)
ax[2].plot(ts, xs, color="#999", lw=.8); ax[2].plot(ts, xs, "o", ms=3.5, color="#1f62b8")
ax[2].set_xlabel("time (s)"); ax[2].set_title("O1, one second = 128 individual samples")
for a in ax: a.set_ylabel("µV")
plt.tight_layout(); plt.show()

# %% [04-signal-quality]
cq = df[[f"cq.{ch}" for ch in CH]].copy(); cq.columns = CH
share = pd.DataFrame({g: (cq == g).mean() * 100 for g in range(5)})
share.columns = [f"grade {g} (%)" for g in range(5)]
share.round(1)

# %% [04-signal-quality]
fig, ax = plt.subplots(3, 1, figsize=(10, 6.5), sharex=True)
ax[0].plot(t / 60, df["cq.p7"], color="#e8590c"); ax[0].set_ylabel("cq.p7 (0–4)")
ax[1].plot(t / 60, df["cq.overall"], color="#1f62b8"); ax[1].set_ylabel("cq.overall (%)")
sq_rows = df["sq.overallsensorquality"].dropna().index
ax[2].plot(t[sq_rows] / 60, df.loc[sq_rows, "sq.overallsensorquality"], color="#2f9e44")
ax[2].set_ylabel("sq.overall (0–100)"); ax[2].set_xlabel("time (min)")
plt.tight_layout(); plt.show()
print("corr(cq.overall, cq.p7) =", round(df["cq.overall"].corr(df["cq.p7"]), 3))

# %% [04-signal-quality]
# sq is available at 2 Hz: look up the cq value on the same rows
rows = df["sq.af3.signalquality"].dropna().index
pd.crosstab(df.loc[rows, "cq.af3"].rename("cq.af3"), df.loc[rows, "sq.af3.signalquality"].rename("sq.af3 grade"))

# %% [04-signal-quality]
def trailing_rms(x, rows, L):
    """RMS of the L samples ending at each index in `rows`."""
    return np.array([np.sqrt(np.mean(x[max(0, i - L + 1): i + 1] ** 2)) for i in rows])

x = df["eeg.af3"].to_numpy()
rows = df["sq.af3.rms"].dropna().index.to_numpy()
dev = df.loc[rows, "sq.af3.rms"].to_numpy()

res = {L: np.corrcoef(trailing_rms(x, rows, L), dev)[0, 1] for L in (64, 128, 256, 384, 512)}
print({L: round(r, 3) for L, r in res.items()})

L = max(res, key=res.get)
mine = trailing_rms(x, rows, L)
fig, ax = plt.subplots(figsize=(4.6, 4))
ax.loglog(dev, mine, ".", ms=3, alpha=.5); lim = [8, 500]; ax.plot(lim, lim, "r--")
ax.set_xlabel("device sq.af3.rms (µV)"); ax.set_ylabel(f"my RMS, window {L} samples (µV)")
ax.set_title(f"AF3, r = {res[L]:.3f}"); plt.show()

# %% [04-signal-quality]
mot = df.dropna(subset=["mot.q0"])
tm = t[mot.index]
qn = np.sqrt((mot[["mot.q0", "mot.q1", "mot.q2", "mot.q3"]] ** 2).sum(axis=1))
acc = mot[["mot.accx", "mot.accy", "mot.accz"]]
sat = (acc.abs() >= 3.99).any(axis=1)
t_sat = tm[sat.to_numpy()][0]
print(f"quaternion norm: median {qn.median():.4f}, fraction within 1±0.01: {(abs(qn - 1) < .01).mean():.3f}")
print(f"accelerometer saturated (|a| ≥ 4 g) on {sat.mean() * 100:.0f}% of motion samples, first at t = {t_sat:.0f} s")

fig, ax = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
ax[0].plot(tm, acc.values, lw=.6); ax[0].set_ylabel("acceleration (g)"); ax[0].legend(["x", "y", "z"], ncol=3)
ax[0].axvline(t_sat, color="r", ls="--")
ax[1].plot(tm, qn, lw=.6); ax[1].set_ylabel("quaternion norm"); ax[1].set_xlabel("time (s)")
plt.tight_layout(); plt.show()

# %% [04-signal-quality]
X = df[[f"eeg.{ch}" for ch in CH]].to_numpy().T               # shape (14 channels, N samples)
n_ep = X.shape[1] // FS
E1 = X[:, :n_ep * FS].reshape(len(CH), n_ep, FS)               # (channel, epoch, sample)
ptp1 = E1.max(axis=2) - E1.min(axis=2)                          # peak-to-peak per epoch

for thr in (100, 150, 200, 300, 500):
    ok = ptp1 < thr
    print(f"threshold {thr:3d} µV: kept per channel {ok.mean() * 100:4.0f}% on average, all 14 channels clean: {ok.all(axis=0).mean() * 100:4.0f}%")

THR = 200
good = ptp1 < THR
fig, ax = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"width_ratios": [1, 1.6]})
ax[0].barh(CH[::-1], good.mean(axis=1)[::-1] * 100, color="#1f62b8"); ax[0].set_xlabel("epochs kept (%)")
ax[0].set_title(f"Peak-to-peak < {THR} µV")
bins = n_ep // 52
img = 1 - good[:, :bins * 52].reshape(len(CH), bins, 52).mean(axis=2)
im = ax[1].imshow(img, aspect="auto", cmap="Reds", extent=[0, t[-1] / 60, len(CH), 0], vmin=0, vmax=1)
ax[1].set_yticks(np.arange(len(CH)) + .5); ax[1].set_yticklabels(CH, fontsize=8); ax[1].set_xlabel("time (min)")
ax[1].set_title("Fraction of bad epochs over time"); ax[1].grid(False); plt.colorbar(im, ax=ax[1])
plt.tight_layout(); plt.show()

# %% [05-statistics]
desc = pd.DataFrame({
    "mean": X.mean(axis=1),
    "std": X.std(axis=1, ddof=1),
    "median": np.median(X, axis=1),
    "MAD (scaled)": stats.median_abs_deviation(X, axis=1, scale="normal"),
    "skewness": stats.skew(X, axis=1),
    "excess kurtosis": stats.kurtosis(X, axis=1),
}, index=CH)
desc.round(2)

# %% [05-statistics]
x = X[CH.index("af3")]
mu, sd = x.mean(), x.std()
fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
ax[0].hist(x, bins=200, density=True, color="#9bb8e0", label="data")
g = np.linspace(-400, 400, 400); ax[0].plot(g, stats.norm.pdf(g, mu, sd), "r", label="normal fit")
ax[0].set_yscale("log"); ax[0].set_ylim(1e-7, 1e-1); ax[0].set_xlabel("AF3 (µV)"); ax[0].set_ylabel("density (log)"); ax[0].legend()
stats.probplot(x[::5], dist="norm", plot=ax[1]); ax[1].set_title("Q–Q plot, AF3"); ax[1].get_lines()[1].set_color("r")
plt.tight_layout(); plt.show()

# %% [05-statistics]
def acf(x, nlags):
    x = x - x.mean(); n = len(x)
    f = np.fft.rfft(x, 2 * n)
    r = np.fft.irfft(f * np.conj(f))[:nlags + 1]
    return r / r[0]

rho = acf(x, 2 * FS)
k_cut = np.argmax(rho < 0.05)                 # first lag where correlation has died out
tau = 1 + 2 * rho[1:k_cut].sum()
N = len(x); N_eff = N / tau
print(f"correlation dies out after {k_cut} lags = {k_cut / FS * 1e3:.0f} ms")
print(f"N = {N},  N_eff ≈ {N_eff:.0f}  (one independent sample every {tau:.1f} samples)")

# 95% confidence interval of the mean: naive vs corrected vs block bootstrap (10-s blocks)
m = x.mean()
se_naive = x.std(ddof=1) / np.sqrt(N)
se_eff = x.std(ddof=1) / np.sqrt(N_eff)
blocks = x[:N // 1280 * 1280].reshape(-1, 1280).mean(axis=1)
rng = np.random.default_rng(0)
boot = rng.choice(blocks, size=(2000, len(blocks))).mean(axis=1)
print(f"mean = {m:.3f} µV")
print(f"naive          95% CI half-width: ±{1.96 * se_naive:.3f} µV")
print(f"N_eff-corrected 95% CI half-width: ±{1.96 * se_eff:.3f} µV")
print(f"block bootstrap 95% CI half-width: ±{(np.percentile(boot, 97.5) - np.percentile(boot, 2.5)) / 2:.3f} µV")

fig, ax = plt.subplots(figsize=(7, 2.8)); ax.stem(np.arange(0, 2 * FS + 1) / FS, rho, markerfmt=" ", basefmt=" ")
ax.set_xlabel("lag (s)"); ax.set_ylabel("ρ(lag)"); ax.set_title("Autocorrelation of AF3"); plt.show()

# %% [05-statistics]
fig, ax = plt.subplots(1, 4, figsize=(11, 2.8), sharey=True)
kur = []
for a, n in zip(ax, (1, 16, 128, 1280)):
    mb = x[:N // n * n].reshape(-1, n).mean(axis=1)
    z = (mb - mb.mean()) / mb.std()
    a.hist(z, bins=80, range=(-5, 5), density=True, color="#9bb8e0")
    g = np.linspace(-5, 5, 200); a.plot(g, stats.norm.pdf(g), "r", lw=1)
    kur.append(stats.kurtosis(z))
    a.set_title(f"n = {n}\nexcess kurtosis {kur[-1]:.1f}", fontsize=9); a.set_xlabel("standardised mean")
plt.tight_layout(); plt.show()

# %% [05-statistics]
R = np.corrcoef(X)
iu = np.triu_indices(len(CH), 1)
dist = np.array([np.hypot(POS[CH[i]][0] - POS[CH[j]][0], POS[CH[i]][1] - POS[CH[j]][1]) for i, j in zip(*iu)])
rho_s, p_s = stats.spearmanr(dist, R[iu])

fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.2), gridspec_kw={"width_ratios": [1.1, 1]})
im = ax[0].imshow(R, cmap="RdBu_r", vmin=-1, vmax=1); ax[0].grid(False)
ax[0].set_xticks(range(14)); ax[0].set_xticklabels(CH, rotation=90, fontsize=8)
ax[0].set_yticks(range(14)); ax[0].set_yticklabels(CH, fontsize=8); plt.colorbar(im, ax=ax[0], fraction=.046)
ax[0].set_title("Pearson correlation")
ax[1].scatter(dist, R[iu], s=14); ax[1].set_xlabel("distance between electrodes (head radius = 1)"); ax[1].set_ylabel("r")
ax[1].set_title(f"Spearman ρ = {rho_s:.2f}")
plt.tight_layout(); plt.show()

# %% [05-statistics]
ls = np.log10(E1.std(axis=2))          # (channel, epoch): log10 of the epoch standard deviation

# (a) Left vs right homologous pairs: PAIRED tests, 7 families -> Holm correction
pairs = [("af3", "af4"), ("f3", "f4"), ("f7", "f8"), ("fc5", "fc6"), ("t7", "t8"), ("p7", "p8"), ("o1", "o2")]
rows = []
for L_, R_ in pairs:
    d = ls[CH.index(L_)] - ls[CH.index(R_)]
    tt = stats.ttest_1samp(d, 0)
    rows.append([f"{L_.upper()} − {R_.upper()}", d.mean(), d.mean() / d.std(ddof=1), tt.statistic, tt.pvalue,
                 stats.wilcoxon(d).pvalue])
res = pd.DataFrame(rows, columns=["pair", "mean diff (log10 µV)", "Cohen d_z", "t", "p (t-test)", "p (Wilcoxon)"]).set_index("pair")

p = res["p (t-test)"].to_numpy(); order = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
for rank, i in enumerate(order):                          # Holm step-down adjustment
    run = max(run, (m - rank) * p[i]); adj[i] = min(1, run)
res["p Holm"] = adj
res

# %% [05-statistics]
# (b) Does the amplitude of P7 differ when its contact grade is 0 vs >= 2?  Two INDEPENDENT groups -> Welch t-test
cq_ep = df["cq.p7"].to_numpy()[:n_ep * FS].reshape(n_ep, FS).mean(axis=1)
y = ls[CH.index("p7")]
bad_c, good_c = y[cq_ep < 0.5], y[cq_ep >= 2]
tw = stats.ttest_ind(bad_c, good_c, equal_var=False)
mw = stats.mannwhitneyu(bad_c, good_c)
diff = bad_c.mean() - good_c.mean()
se = np.sqrt(bad_c.var(ddof=1) / len(bad_c) + good_c.var(ddof=1) / len(good_c))
sp = np.sqrt(((len(bad_c) - 1) * bad_c.var(ddof=1) + (len(good_c) - 1) * good_c.var(ddof=1)) / (len(bad_c) + len(good_c) - 2))
print(f"epochs: cq=0 -> {len(bad_c)},  cq>=2 -> {len(good_c)}")
print(f"mean log10 std: {bad_c.mean():.3f} vs {good_c.mean():.3f}  (ratio of amplitudes x{10 ** diff:.2f})")
print(f"Welch t = {tw.statistic:.2f}, p = {tw.pvalue:.2e};  Mann-Whitney p = {mw.pvalue:.2e}")
print(f"95% CI of the difference: [{diff - 1.96 * se:.3f}, {diff + 1.96 * se:.3f}],  Cohen d = {diff / sp:.2f}")
r1 = np.corrcoef(y[:-1], y[1:])[0, 1]; print(f"lag-1 autocorrelation of the epoch feature: {r1:.2f}")

# %% [06-sampling-fourier]
fs_demo = 128
tc = np.linspace(0, 0.1, 5000)                     # "continuous" time (fine grid)
ts_ = np.arange(0, 0.1, 1 / fs_demo)               # sampling instants

f_true = 100; f_alias = abs(f_true - round(f_true / fs_demo) * fs_demo)
fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(tc, np.cos(2 * np.pi * f_true * tc), color="#1f62b8", lw=.8, label=f"true {f_true} Hz")
ax.plot(tc, np.cos(2 * np.pi * f_alias * tc), color="crimson", lw=.8, ls="--", label=f"alias {f_alias} Hz")
ax.plot(ts_, np.cos(2 * np.pi * f_true * ts_), "ko", label="samples at 128 Hz")
ax.set_xlabel("time (s)"); ax.legend(loc="upper right", fontsize=8, ncol=3); plt.show()
print("max difference between the two sampled signals:",
      np.abs(np.cos(2 * np.pi * f_true * ts_) - np.cos(2 * np.pi * f_alias * ts_)).max())

# %% [06-sampling-fourier]
import time
N_ = 2048
rng_ = np.random.default_rng(1); xr = rng_.standard_normal(N_)
n_ = np.arange(N_); W = np.exp(-2j * np.pi * np.outer(n_, n_) / N_)       # N x N DFT matrix

t0 = time.perf_counter(); X_mat = W @ xr; t_mat = time.perf_counter() - t0
t0 = time.perf_counter(); X_fft = np.fft.fft(xr); t_fft = time.perf_counter() - t0
print("same result:", np.allclose(X_mat, X_fft))
print(f"matrix DFT: {t_mat * 1e3:.1f} ms,  FFT: {t_fft * 1e3:.2f} ms  (about x{t_mat / t_fft:.0f} faster)")

# %% [06-sampling-fourier]
fs_, N_ = 128, 512                                  # 4 s -> resolution 0.25 Hz
tt = np.arange(N_) / fs_
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
for a, f0 in zip(ax, (10.0, 10.3)):
    x_ = np.sin(2 * np.pi * f0 * tt)
    for name, w in (("rectangular", np.ones(N_)), ("Hann", np.hanning(N_))):
        A = np.abs(np.fft.rfft(x_ * w)) / w.sum() * 2
        a.plot(np.fft.rfftfreq(N_, 1 / fs_), 20 * np.log10(A + 1e-12), label=name)
    a.set_xlim(5, 16); a.set_ylim(-120, 5); a.set_xlabel("frequency (Hz)"); a.set_title(f"{f0} Hz sinusoid (Δf = {fs_ / N_} Hz)")
ax[0].set_ylabel("amplitude (dB)"); ax[0].legend(); plt.tight_layout(); plt.show()

# %% [06-sampling-fourier]
ok = (ptp1[CH.index("o1")] < 150) & (ptp1[CH.index("o2")] < 150)
start = next(k for k in range(60, n_ep - 8) if ok[k:k + 8].all())          # first clean 8 s after t = 60 s
s0, s1 = start * FS, (start + 8) * FS
xs = X[CH.index("o1"), s0:s1]; xs = xs - xs.mean()
w = np.hanning(len(xs))
A = np.abs(np.fft.rfft(xs * w)) / w.sum() * 2          # amplitude (µV), corrected for the window gain
fq = np.fft.rfftfreq(len(xs), 1 / FS)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.2))
ax[0].plot(np.arange(s0, s1) / FS, xs); ax[0].set_xlabel("time (s)"); ax[0].set_ylabel("O1 (µV)"); ax[0].set_title(f"clean segment from t = {start} s")
ax[1].plot(fq, A); ax[1].set_xlim(0, 45); ax[1].set_xlabel("frequency (Hz)"); ax[1].set_ylabel("amplitude (µV)"); ax[1].set_title("Amplitude spectrum")
ax[2].loglog(fq[1:], A[1:]); ax[2].set_xlabel("frequency (Hz)"); ax[2].set_title("Same, log–log")
plt.tight_layout(); plt.show()

# Parseval: energy in time = energy in frequency
Xf = np.fft.fft(xs)
print("sum x^2        =", round(float(np.sum(xs ** 2)), 1))
print("sum |X|^2 / N  =", round(float(np.sum(np.abs(Xf) ** 2) / len(xs)), 1))

# %% [06-sampling-fourier]
rng_ = np.random.default_rng(0)
for N_w in (1000, 100_000):
    xw = rng_.standard_normal(N_w)
    f_, P_ = signal.periodogram(xw, fs=FS, window="boxcar")
    P_ = P_[1:-1]
    print(f"N = {N_w:>7}: relative std of the periodogram = {P_.std() / P_.mean():.2f}  (true PSD is flat)")

# %% [06-sampling-fourier]
x = X[CH.index("o1")]
fig, ax = plt.subplots(figsize=(10, 3.8))
f_p, P_p = signal.periodogram(x, fs=FS, window="hann")
ax.semilogy(f_p, P_p, color="#cccccc", lw=.5, label="periodogram (N = 199,705)")
for nseg, col in ((1024, "#2f9e44"), (256, "#1f62b8"), (64, "#e8590c")):
    f_w, P_w = signal.welch(x, fs=FS, nperseg=nseg)
    ax.semilogy(f_w, P_w, color=col, lw=1.4, label=f"Welch, nperseg = {nseg} (Δf = {FS / nseg:.2f} Hz)")
ax.set_xlim(0, 64); ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("PSD (µV²/Hz)"); ax.legend(fontsize=8); plt.show()

# approximate 95% confidence interval for a Welch estimate with K segments (50% overlap): chi-square with ~2K d.o.f.
for nseg in (1024, 256, 64):
    K = 2 * len(x) // nseg - 1; nu = 2 * K * 0.9 if K > 1 else 2
    print(f"nperseg {nseg:5d}: K = {K:5d}, 95% CI of the PSD: x[{nu / stats.chi2.ppf(.975, nu):.2f}, {nu / stats.chi2.ppf(.025, nu):.2f}]")

# %% [07-filtering]
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.6))
for order in (2, 4, 8):
    sos = signal.butter(order, [1, 40], btype="bandpass", fs=FS, output="sos")
    w, h = signal.sosfreqz(sos, worN=4096, fs=FS)
    ax[0].plot(w, 20 * np.log10(np.abs(h) + 1e-12), label=f"order {order}")
    ax[1].plot(w, np.unwrap(np.angle(h)), label=f"order {order}")
ax[0].axhline(-3, color="k", ls=":", lw=.8); ax[0].set_ylim(-60, 5); ax[0].set_xlim(0, 64)
ax[0].set_xlabel("frequency (Hz)"); ax[0].set_ylabel("gain (dB)"); ax[0].set_title("Magnitude response (dotted: −3 dB)"); ax[0].legend()
ax[1].set_xlim(0, 64); ax[1].set_xlabel("frequency (Hz)"); ax[1].set_ylabel("phase (rad)"); ax[1].set_title("Phase response")
plt.tight_layout(); plt.show()

# %% [07-filtering]
tt = np.arange(0, 4, 1 / FS)
burst = np.sin(2 * np.pi * 10 * tt) * np.exp(-((tt - 2) / 0.35) ** 2)          # 10 Hz burst centred at t = 2 s
sos_a = signal.butter(4, [8, 13], btype="bandpass", fs=FS, output="sos")

y_causal = signal.sosfilt(sos_a, burst)
y_zero = signal.sosfiltfilt(sos_a, burst)
lag = (np.argmax(np.abs(signal.hilbert(y_causal))) - np.argmax(np.abs(signal.hilbert(y_zero))))
print(f"envelope peak delay of the causal output: {lag} samples = {lag / FS * 1e3:.0f} ms")

fig, ax = plt.subplots(figsize=(10, 3))
ax.plot(tt, burst, color="#bbbbbb", lw=3, label="input burst")
ax.plot(tt, y_causal, color="crimson", label="causal (sosfilt): delayed")
ax.plot(tt, y_zero, color="#1f62b8", label="zero-phase (sosfiltfilt): aligned")
ax.set_xlabel("time (s)"); ax.legend(fontsize=8, loc="upper right"); plt.show()

# %% [07-filtering]
def bandpass(x, lo, hi, order=4, axis=-1):
    """Zero-phase Butterworth band-pass (lo, hi in Hz) applied along `axis`."""
    sos = signal.butter(order, [lo, hi], btype="bandpass", fs=FS, output="sos")
    return signal.sosfiltfilt(sos, x, axis=axis)

Xf = bandpass(X, 1, 40)                                   # filtered copy of all channels, (14, N)

i = CH.index("o1")
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [1.2, 1]})
ts_, sl = np.arange(len(X[0])) / FS, slice(start * FS, (start + 10) * FS)
ax[0].plot(ts_[sl], X[i, sl], color="#bbbbbb", label="raw"); ax[0].plot(ts_[sl], Xf[i, sl], color="#1f62b8", label="1–40 Hz")
ax[0].set_xlabel("time (s)"); ax[0].set_ylabel("O1 (µV)"); ax[0].legend(); ax[0].set_title("A clean 10-s stretch")
for arr, col, lab in ((X, "#bbbbbb", "raw"), (Xf, "#1f62b8", "filtered")):
    f_, P_ = signal.welch(arr[i], fs=FS, nperseg=256); ax[1].semilogy(f_, P_, color=col, label=lab)
ax[1].set_xlabel("frequency (Hz)"); ax[1].set_ylabel("PSD (µV²/Hz)"); ax[1].set_title("O1 spectrum"); ax[1].legend()
plt.tight_layout(); plt.show()
print("std of O1 before / after filtering:", X[i].std().round(1), "/", Xf[i].std().round(1), "µV")

# %% [07-filtering]
x_clean = Xf[i, start * FS:(start + 20) * FS]
tt20 = np.arange(len(x_clean)) / FS
x_noisy = x_clean + 20 * np.sin(2 * np.pi * 50 * tt20)                       # mains contamination

b, a = signal.iirnotch(50, Q=30, fs=FS)
x_fixed = signal.filtfilt(b, a, x_noisy)

fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.4))
w, h = signal.freqz(b, a, worN=4096, fs=FS)
ax[0].plot(w, 20 * np.log10(np.abs(h))); ax[0].set_xlim(30, 64); ax[0].set_xlabel("frequency (Hz)"); ax[0].set_ylabel("gain (dB)"); ax[0].set_title("Notch response, Q = 30")
for arr, lab, col in ((x_noisy, "with 50 Hz", "crimson"), (x_fixed, "after notch", "#1f62b8")):
    f_, P_ = signal.welch(arr, fs=FS, nperseg=256); ax[1].semilogy(f_, P_, label=lab, color=col)
ax[1].set_xlabel("frequency (Hz)"); ax[1].set_ylabel("PSD (µV²/Hz)"); ax[1].legend(); ax[1].set_title("Spectrum")
plt.tight_layout(); plt.show()

f_all, P_all = signal.welch(X[i], fs=FS, nperseg=256)
print(f"real O1 raw data: PSD at 50 Hz = {P_all[np.argmin(abs(f_all - 50))]:.2f} µV²/Hz vs {P_all[np.argmin(abs(f_all - 10))]:.1f} at 10 Hz")

# %% [07-filtering]
taps = signal.firwin(257, [8, 13], pass_zero=False, fs=FS, window="hamming")
w1, h1 = signal.freqz(taps, 1, worN=4096, fs=FS)
w2, h2 = signal.sosfreqz(sos_a, worN=4096, fs=FS)
fig, ax = plt.subplots(figsize=(8, 3.3))
ax.plot(w1, 20 * np.log10(np.abs(h1) + 1e-12), label="FIR, 257 taps"); ax.plot(w2, 20 * np.log10(np.abs(h2) + 1e-12), label="Butterworth, order 4 (x2 with filtfilt)")
ax.set_xlim(0, 30); ax.set_ylim(-80, 5); ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("gain (dB)"); ax.legend(); plt.show()
print(f"FIR delay = (257-1)/2 = {(len(taps) - 1) // 2} samples = {(len(taps) - 1) / 2 / FS:.1f} s; use signal.filtfilt or compensate it")

# %% [08-rhythms]
NS_ = 2 * FS                                                  # 256 samples per epoch
n2 = Xf.shape[1] // NS_
E2 = Xf[:, :n2 * NS_].reshape(len(CH), n2, NS_)               # (channel, epoch, sample)
ptp2 = E2.max(axis=2) - E2.min(axis=2)
good2 = ptp2 < 200                                            # per-channel mask (True = keep)

PSD = []
for k in range(len(CH)):
    f_psd, Pk = signal.periodogram(E2[k, good2[k]], fs=FS, window="hann", axis=-1)
    PSD.append(Pk.mean(axis=0))                               # average over clean epochs
PSD = np.array(PSD)                                           # (14, n_freq), µV²/Hz
print("epochs kept per channel (of", n2, "):", dict(zip(CH, good2.sum(axis=1))))

fig, ax = plt.subplots(figsize=(10, 4))
for k, ch in enumerate(CH):
    ax.semilogy(f_psd, PSD[k], color=COLORS[REGION[ch]], lw=1, alpha=.85)
for reg, col in COLORS.items(): ax.plot([], [], color=col, label=reg)
for lo, hi, col in ((1, 4, "#7048e8"), (4, 8, "#2f80ed"), (8, 13, "#2f9e44"), (13, 30, "#e8590c")):
    ax.axvspan(lo, hi, color=col, alpha=.07)
ax.set_xlim(1, 40); ax.set_ylim(.05, 500); ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("PSD (µV²/Hz)"); ax.legend(ncol=4, fontsize=8)
ax.set_title("Clean PSD of the 14 channels (shading: delta, theta, alpha, beta)"); plt.show()

# %% [08-rhythms]
BANDS = {"delta": (1, 4), "theta": (4, 8), "alpha": (8, 13), "beta": (13, 30), "low gamma": (30, 40)}

def bandpower(P, f, lo, hi):
    """Integrate PSD `P` (last axis) over [lo, hi) Hz with the trapezoid rule."""
    m = (f >= lo) & (f < hi)
    return np.trapezoid(P[..., m], f[m], axis=-1)

total = bandpower(PSD, f_psd, 1, 40)
rel = pd.DataFrame({b: bandpower(PSD, f_psd, lo, hi) / total for b, (lo, hi) in BANDS.items()}, index=CH)

fig, ax = plt.subplots(figsize=(7, 4.4))
im = ax.imshow(rel.values * 100, cmap="viridis", aspect="auto"); ax.grid(False)
ax.set_xticks(range(5)); ax.set_xticklabels(rel.columns); ax.set_yticks(range(14)); ax.set_yticklabels(CH)
for (r_, c_), v in np.ndenumerate(rel.values * 100): ax.text(c_, r_, f"{v:.0f}", ha="center", va="center", color="w", fontsize=8)
plt.colorbar(im, label="relative power (%)"); ax.set_title("Relative band power per channel"); plt.show()
(rel * 100).round(1)

# %% [08-rhythms]
S = PSD[[CH.index("o1"), CH.index("o2")]].mean(axis=0)
fit_mask = ((f_psd >= 2) & (f_psd < 7)) | ((f_psd >= 16) & (f_psd < 30))   # avoid the 40 Hz filter edge
lr = stats.linregress(np.log10(f_psd[fit_mask]), np.log10(S[fit_mask]))
bg = 10 ** (lr.intercept + lr.slope * np.log10(f_psd[1:]))
resid_db = 10 * np.log10(S[1:] / bg)
pk = (f_psd[1:] >= 7) & (f_psd[1:] <= 16)
f_peak = f_psd[1:][pk][np.argmax(resid_db[pk])]
print(f"aperiodic exponent chi = {-lr.slope:.2f},  R² of the fit = {lr.rvalue ** 2:.3f}")
print(f"oscillatory peak at {f_peak:.1f} Hz, {resid_db[pk].max():.1f} dB above the background")

fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.6))
fm = f_psd[1:] <= 40
ax[0].loglog(f_psd[1:][fm], S[1:][fm], label="mean O1/O2"); ax[0].loglog(f_psd[1:][fm], bg[fm], "r--", label=f"1/f^{-lr.slope:.2f} fit")
ax[0].set_xlabel("frequency (Hz)"); ax[0].set_ylabel("PSD (µV²/Hz)"); ax[0].legend()
ax[1].plot(f_psd[1:][fm], resid_db[fm]); ax[1].axhline(0, color="k", lw=.6); ax[1].axvline(f_peak, color="crimson", ls=":")
ax[1].set_xlim(1, 40); ax[1].set_ylim(-10, 15); ax[1].set_xlabel("frequency (Hz)"); ax[1].set_ylabel("above background (dB)"); ax[1].set_title("Residual = oscillatory component")
plt.tight_layout(); plt.show()

# %% [08-rhythms]
i = CH.index("o1")
def spec(x, nperseg):
    f, tt, Sxx = signal.spectrogram(x, fs=FS, nperseg=nperseg, noverlap=nperseg // 2, window="hann")
    return f, tt, 10 * np.log10(Sxx + 1e-12)

fig = plt.figure(figsize=(11, 6.6)); gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1])
f, tt, Sdb = spec(Xf[i], 256)
a0 = fig.add_subplot(gs[0, :]); m = f <= 40
im = a0.pcolormesh(tt / 60, f[m], Sdb[m], shading="auto", cmap="magma", vmin=-10, vmax=30)
a0.set_ylabel("frequency (Hz)"); a0.set_xlabel("time (min)"); a0.set_title("O1 spectrogram, whole recording (2-s windows)"); a0.grid(False)
plt.colorbar(im, ax=a0, label="dB re 1 µV²/Hz")
for col, nseg in enumerate((64, 512)):
    a = fig.add_subplot(gs[1, col]); seg0 = int(300 * FS); seg1 = int(420 * FS)
    f, tt, Sdb = spec(Xf[i, seg0:seg1], nseg); m = f <= 40
    a.pcolormesh(300 + tt, f[m], Sdb[m], shading="auto", cmap="magma", vmin=-10, vmax=30)
    a.set_title(f"zoom 300–420 s, window {nseg / FS:.1f} s (Δf = {FS / nseg:.2f} Hz)"); a.set_xlabel("time (s)"); a.grid(False)
plt.tight_layout(); plt.show()

# %% [08-rhythms]
alpha_o1 = bandpass(X[CH.index("o1")], 8, 13)
env = np.abs(signal.hilbert(alpha_o1))

s0_, s1_ = int(start * FS), int((start + 6) * FS)
fig, ax = plt.subplots(2, 1, figsize=(10, 5), sharex=False)
tt = np.arange(s0_, s1_) / FS
ax[0].plot(tt, alpha_o1[s0_:s1_], lw=.8, label="alpha-filtered O1"); ax[0].plot(tt, env[s0_:s1_], "r", label="envelope |z|")
ax[0].plot(tt, -env[s0_:s1_], "r"); ax[0].set_ylabel("µV"); ax[0].legend(fontsize=8); ax[0].set_xlabel("time (s)")

# per-epoch alpha power over the session (clean epochs only), smoothed over 30 epochs
ep_pow = np.where(good2[CH.index("o1")], np.log10((E2[CH.index("o1")] ** 2).mean(axis=1) + 1e-9), np.nan)
ep_alpha = bandpower(signal.periodogram(E2[CH.index("o1")], fs=FS, window="hann", axis=-1)[1], f_psd, 8, 13)
ep_alpha = np.where(good2[CH.index("o1")], np.log10(ep_alpha), np.nan)
sm = pd.Series(ep_alpha).rolling(30, min_periods=10, center=True).median()
ax[1].plot(np.arange(n2) * 2 / 60, ep_alpha, ".", ms=2, color="#bbbbbb"); ax[1].plot(np.arange(n2) * 2 / 60, sm, color="#2f9e44")
ax[1].set_xlabel("time (min)"); ax[1].set_ylabel("log10 alpha power, O1"); ax[1].set_title("Clean 2-s epochs (dots) and 1-minute rolling median")
plt.tight_layout(); plt.show()

# %% [08-rhythms]
from scipy.interpolate import RBFInterpolator

def topomap(values, ax, title="", cmap="viridis", vmin=None, vmax=None, chs=None):
    """Smooth interpolation of one value per electrode on the schematic head."""
    pts = np.array([POS[ch] for ch in (chs or CH)])
    rbf = RBFInterpolator(pts, np.asarray(values, float), kernel="thin_plate_spline", smoothing=1e-2)
    g = np.linspace(-1.12, 1.12, 140); gx, gy = np.meshgrid(g, g)
    z = rbf(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape); z[np.hypot(gx, gy) > 1.12] = np.nan
    im = ax.imshow(z, extent=[-1.12, 1.12, -1.12, 1.12], origin="lower", cmap=cmap, vmin=vmin, vmax=vmax)
    ax.scatter(pts[:, 0], pts[:, 1], c="k", s=12, zorder=3); draw_head(ax); ax.set_title(title)
    return im

USE13 = [ch for ch in CH if ch != "p7"]                     # P7 left out: its contact is poor
fig, ax = plt.subplots(1, 3, figsize=(11, 3.8))
for a, band in zip(ax, ("theta", "alpha", "beta")):
    im = topomap(rel.loc[USE13, band].values * 100, a, f"{band}: relative power (%)", chs=USE13)
    plt.colorbar(im, ax=a, fraction=.046)
plt.tight_layout(); plt.show()

# %% [09-lab-pipeline]
USE = [ch for ch in CH if ch != "p7"]                  # P7: contact grade 0 half of the time
idx = [CH.index(ch) for ch in USE]

keep = good2[idx].all(axis=0)                           # epochs clean on ALL 13 retained channels
print(f"{len(USE)} channels kept; {keep.sum()} of {n2} epochs kept ({keep.mean() * 100:.0f}%) = {keep.sum() * 2 / 60:.1f} min of data")

f_e, Pall = signal.periodogram(E2, fs=FS, window="hann", axis=-1)        # (14, n2, n_freq)
bp = {b: bandpower(Pall, f_e, lo, hi) for b, (lo, hi) in BANDS.items()}   # each (14, n2)
t_ep = (np.arange(n2) * 2 + 1) / 60                                       # epoch centre in minutes
print("band-power arrays:", {b: v.shape for b, v in bp.items()})

# %% [09-lab-pipeline]
def faa(left, right):
    ok = good2[CH.index(left)] & good2[CH.index(right)]
    v = np.log(bp["alpha"][CH.index(right)][ok]) - np.log(bp["alpha"][CH.index(left)][ok])
    return v, t_ep[ok]

rows = []
for L_, R_ in (("f3", "f4"), ("f7", "f8")):
    v, tv = faa(L_, R_)
    n = len(v); r1 = np.corrcoef(v[:-1], v[1:])[0, 1]; n_eff = n * (1 - r1) / (1 + r1)
    tt = stats.ttest_1samp(v, 0)
    se_naive = v.std(ddof=1) / np.sqrt(n); se_adj = v.std(ddof=1) / np.sqrt(n_eff)
    rows.append({"pair": f"{R_.upper()} − {L_.upper()}", "n epochs": n, "mean FAA": v.mean(), "Cohen d": v.mean() / v.std(ddof=1),
                 "lag-1 autocorr": r1, "n_eff": n_eff, "95% CI naive ±": 1.96 * se_naive, "95% CI adjusted ±": stats.t.ppf(.975, n_eff - 1) * se_adj,
                 "p (naive t-test)": tt.pvalue, "p (Wilcoxon)": stats.wilcoxon(v).pvalue})
faa_res = pd.DataFrame(rows).set_index("pair")
faa_res.T

# %% [09-lab-pipeline]
v34, tv34 = faa("f3", "f4")
blocks = np.digitize(tv34, np.arange(5, 26, 5))                  # 5-minute blocks
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.4))
ax[0].hist(v34, bins=40, color="#9bb8e0"); ax[0].axvline(0, color="k", lw=.8); ax[0].axvline(v34.mean(), color="crimson")
ax[0].set_xlabel("FAA, F4 − F3 (ln units)"); ax[0].set_ylabel("epochs"); ax[0].set_title("Distribution (red = mean)")
bm = [v34[blocks == b].mean() for b in np.unique(blocks)]
be = [1.96 * v34[blocks == b].std(ddof=1) / np.sqrt((blocks == b).sum()) for b in np.unique(blocks)]
ax[1].errorbar(np.unique(blocks) * 5 + 2.5, bm, yerr=be, fmt="o-", capsize=3); ax[1].axhline(0, color="k", lw=.8)
ax[1].set_xlabel("time (min, block centre)"); ax[1].set_ylabel("mean FAA ± naive 95% CI"); ax[1].set_title("Stability over the session")
plt.tight_layout(); plt.show()

# %% [09-lab-pipeline]
Z = E2[idx][:, keep, :].reshape(len(idx), -1)             # channels x samples of clean epochs
Zs = (Z - Z.mean(axis=1, keepdims=True)) / Z.std(axis=1, keepdims=True)
U, s_, Vt = np.linalg.svd(Zs, full_matrices=False)
evr = s_ ** 2 / np.sum(s_ ** 2)
print("explained variance of the first 5 components (%):", (evr[:5] * 100).round(1))
print("components needed for 90% of the variance:", int(np.searchsorted(np.cumsum(evr), .90)) + 1)

def topomap_sub(values, ax, title):
    return topomap(values, ax, title, cmap="RdBu_r", vmin=-.6, vmax=.6, chs=USE)

fig, ax = plt.subplots(1, 3, figsize=(11.5, 3.6), gridspec_kw={"width_ratios": [1.1, 1, 1]})
ax[0].bar(range(1, len(evr) + 1), evr * 100, color="#1f62b8"); ax[0].plot(range(1, len(evr) + 1), np.cumsum(evr) * 100, "ko-", ms=3)
ax[0].set_xlabel("component"); ax[0].set_ylabel("explained variance (%)"); ax[0].set_title("Scree plot (line: cumulative)")
for k in (0, 1):
    load = U[:, k] * (1 if U[:, k].mean() >= 0 or k else -1)
    im = topomap_sub(load, ax[k + 1], f"PC{k + 1} loadings ({evr[k] * 100:.0f}%)")
plt.colorbar(im, ax=ax[2], fraction=.046)
plt.tight_layout(); plt.show()

# %% [09-lab-pipeline]
mot = df.dropna(subset=["mot.accx"])
tm = t[mot.index]
amag = np.sqrt((mot[["mot.accx", "mot.accy", "mot.accz"]] ** 2).sum(axis=1)).to_numpy()
ep_of = (tm * FS // NS_).astype(int)                                      # epoch number of every motion sample
acc_int = pd.Series(amag).groupby(ep_of).std()                            # motion intensity per epoch
acc_int = acc_int[(acc_int.index < n2) & ((acc_int.index + 1) * 2 < t_sat)]

eeg_pow = np.log10((E2[idx] ** 2).mean(axis=2) + 1e-9)                    # (13, n2) log power per epoch
eeg_med = np.median(eeg_pow, axis=0)
xm = np.log10(acc_int.values + 1e-4); ym = eeg_med[acc_int.index.to_numpy()]
rho_m, p_m = stats.spearmanr(xm, ym)

fig, ax = plt.subplots(figsize=(5.6, 4))
ax.plot(xm, ym, ".", ms=3, alpha=.5); ax.set_xlabel("log10 motion intensity (std of |acc|, g)"); ax.set_ylabel("median log10 EEG power over channels")
ax.set_title(f"Spearman ρ = {rho_m:.2f} (n = {len(xm)} epochs)"); plt.show()
