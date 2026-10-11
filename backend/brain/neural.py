"""
neural.py - Multi-head embedding-bag neural network (pure numpy)
-----------------------------------------------------------------
Architecture (per ensemble member):

    instruction ids --> EmbeddingBag(mean) --\
    full-text ids   --> EmbeddingBag(mean) ---+--> concat --> Dense(H, ReLU, dropout) --+--> task head   (softmax)
    structural vec  --> standardise ---------/                                         +--> tier head   (softmax)
                                                                                       +--> length head (softmax)

Training: joint cross-entropy with label smoothing, Adam (lazy sparse updates for the
embedding table). An ensemble of independently seeded members gives calibrated
probabilities and an uncertainty estimate (member disagreement).
"""

from typing import Dict, List, Sequence, Tuple

import numpy as np

from .features import NUM_BUCKETS

TASKS = [
    "conversation", "factual", "explanation", "summarization", "translation",
    "creative", "coding", "math", "reasoning", "analysis",
]
TIERS = ["simple", "moderate", "complex", "expert"]
LENGTHS = ["short", "medium", "long"]

HEADS = {"task": TASKS, "tier": TIERS, "length": LENGTHS}
HEAD_LOSS_WEIGHT = {"task": 1.0, "tier": 1.0, "length": 0.5}


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def _bag(E: np.ndarray, id_lists: Sequence[np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    counts = np.fromiter((len(x) for x in id_lists), dtype=np.int64, count=len(id_lists))
    cat = np.concatenate(id_lists)
    offsets = np.concatenate(([0], np.cumsum(counts)[:-1]))
    sums = np.add.reduceat(E[cat], offsets, axis=0)
    seg = np.repeat(np.arange(len(id_lists)), counts)
    return sums / counts[:, None], cat, seg, counts


class _Adam:
    def __init__(self, lr: float, b1: float = 0.9, b2: float = 0.999, eps: float = 1e-8):
        self.lr, self.b1, self.b2, self.eps = lr, b1, b2, eps
        self.m: Dict[str, np.ndarray] = {}
        self.v: Dict[str, np.ndarray] = {}
        self.t = 0

    def dense(self, name: str, p: np.ndarray, g: np.ndarray, wd: float = 0.0):
        if name not in self.m:
            self.m[name] = np.zeros_like(p)
            self.v[name] = np.zeros_like(p)
        if wd:
            g = g + wd * p
        m, v = self.m[name], self.v[name]
        m *= self.b1
        m += (1 - self.b1) * g
        v *= self.b2
        v += (1 - self.b2) * g * g
        mh = m / (1 - self.b1 ** self.t)
        vh = v / (1 - self.b2 ** self.t)
        p -= self.lr * mh / (np.sqrt(vh) + self.eps)

    def rows(self, name: str, p: np.ndarray, rows: np.ndarray, g: np.ndarray):
        if name not in self.m:
            self.m[name] = np.zeros_like(p)
            self.v[name] = np.zeros_like(p)
        mr = self.b1 * self.m[name][rows] + (1 - self.b1) * g
        vr = self.b2 * self.v[name][rows] + (1 - self.b2) * g * g
        self.m[name][rows] = mr
        self.v[name][rows] = vr
        step = (self.lr / (1 - self.b1 ** self.t)) * mr / (np.sqrt(vr / (1 - self.b2 ** self.t)) + self.eps)
        p[rows] -= step


class BagNet:
    def __init__(self, n_struct: int, dim: int = 40, hidden: int = 96, seed: int = 0):
        rng = np.random.default_rng(seed)
        self.dim, self.hidden = dim, hidden
        self.p: Dict[str, np.ndarray] = {
            # Zero init: hash buckets never seen in training stay neutral instead of injecting random noise.
            "E": np.zeros((NUM_BUCKETS, dim), dtype=np.float32),
            "W1": (rng.standard_normal((2 * dim + n_struct, hidden)) * np.sqrt(2.0 / (2 * dim + n_struct))).astype(np.float32),
            "b1": np.zeros(hidden, dtype=np.float32),
        }
        for head, labels in HEADS.items():
            self.p["W_" + head] = (rng.standard_normal((hidden, len(labels))) * np.sqrt(1.0 / hidden)).astype(np.float32)
            self.p["b_" + head] = np.zeros(len(labels), dtype=np.float32)
        self.rng = rng

    def _forward(self, heads_ids, all_ids, struct, train: bool, dropout: float = 0.0):
        hh, cat_h, seg_h, cnt_h = _bag(self.p["E"], heads_ids)
        ha, cat_a, seg_a, cnt_a = _bag(self.p["E"], all_ids)
        x = np.concatenate([hh, ha, struct], axis=1)
        a = x @ self.p["W1"] + self.p["b1"]
        z = np.maximum(a, 0.0)
        mask = None
        if train and dropout > 0:
            mask = (self.rng.random(z.shape) >= dropout).astype(np.float32) / (1.0 - dropout)
            z = z * mask
        probs = {h: _softmax(z @ self.p["W_" + h] + self.p["b_" + h]) for h in HEADS}
        cache = (x, a, z, mask, cat_h, seg_h, cnt_h, cat_a, seg_a, cnt_a)
        return probs, cache

    def predict(self, heads_ids, all_ids, struct) -> Dict[str, np.ndarray]:
        probs, _ = self._forward(heads_ids, all_ids, struct, train=False)
        return probs

    def train_step(self, batch, opt: _Adam, smoothing: float, dropout: float, wd: float) -> float:
        heads_ids, all_ids, struct, labels = batch
        n = struct.shape[0]
        probs, (x, a, z, mask, cat_h, seg_h, cnt_h, cat_a, seg_a, cnt_a) = self._forward(
            heads_ids, all_ids, struct, train=True, dropout=dropout)

        loss = 0.0
        dz = np.zeros_like(z)
        grads: Dict[str, np.ndarray] = {}
        for head, k in ((h, len(l)) for h, l in HEADS.items()):
            y = np.full((n, k), smoothing / k, dtype=np.float32)
            y[np.arange(n), labels[head]] += 1.0 - smoothing
            p = probs[head]
            w = HEAD_LOSS_WEIGHT[head]
            loss += -w * float(np.mean(np.sum(y * np.log(p + 1e-9), axis=1)))
            dl = w * (p - y) / n
            grads["W_" + head] = z.T @ dl
            grads["b_" + head] = dl.sum(axis=0)
            dz += dl @ self.p["W_" + head].T

        if mask is not None:
            dz = dz * mask
        da = dz * (a > 0)
        grads["W1"] = x.T @ da
        grads["b1"] = da.sum(axis=0)
        dx = da @ self.p["W1"].T
        # Embedding gradient: each id in sample i receives dx_i / count_i. Build a sparse
        # (unique id x sample) weight matrix and multiply, instead of scattering every row.
        D = self.dim
        uniq, inv = np.unique(np.concatenate([cat_h, cat_a]), return_inverse=True)
        U, nh = len(uniq), len(cat_h)
        s_h = np.bincount(inv[:nh] * n + seg_h, weights=1.0 / cnt_h[seg_h], minlength=U * n).reshape(U, n)
        s_a = np.bincount(inv[nh:] * n + seg_a, weights=1.0 / cnt_a[seg_a], minlength=U * n).reshape(U, n)
        gE = (s_h.astype(np.float32) @ dx[:, :D] + s_a.astype(np.float32) @ dx[:, D:2 * D]).astype(np.float32)

        opt.t += 1
        for name, g in grads.items():
            opt.dense(name, self.p[name], g.astype(np.float32), wd=wd if name.startswith("W") else 0.0)
        opt.rows("E", self.p["E"], uniq, gE)
        return loss


class Ensemble:
    def __init__(self, members: List[BagNet], mu: np.ndarray, sigma: np.ndarray):
        self.members, self.mu, self.sigma = members, mu, sigma

    def _std(self, struct: np.ndarray) -> np.ndarray:
        return ((struct - self.mu) / self.sigma).astype(np.float32)

    def predict(self, heads_ids, all_ids, struct) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        s = self._std(struct)
        outs = [m.predict(heads_ids, all_ids, s) for m in self.members]
        mean = {h: np.mean([o[h] for o in outs], axis=0) for h in HEADS}
        spread = {h: np.mean([np.abs(o[h] - mean[h]).sum(axis=1) for o in outs], axis=0) / 2.0 for h in HEADS}
        return mean, spread

    # -- persistence ------------------------------------------------------
    def save(self, path: str, fingerprint: str):
        blob = {"mu": self.mu, "sigma": self.sigma, "fingerprint": np.array(fingerprint),
                "n_members": np.array(len(self.members)),
                "dim": np.array(self.members[0].dim), "hidden": np.array(self.members[0].hidden)}
        for i, m in enumerate(self.members):
            for k, v in m.p.items():
                blob[f"m{i}_{k}"] = v.astype(np.float16) if k == "E" else v
        np.savez_compressed(path, **blob)

    @classmethod
    def load(cls, path: str, fingerprint: str):
        data = np.load(path, allow_pickle=False)
        if str(data["fingerprint"]) != fingerprint:
            return None
        mu, sigma = data["mu"], data["sigma"]
        members = []
        for i in range(int(data["n_members"])):
            m = BagNet(len(mu), dim=int(data["dim"]), hidden=int(data["hidden"]), seed=i)
            for k in m.p:
                m.p[k] = data[f"m{i}_{k}"].astype(np.float32)
            members.append(m)
        return cls(members, mu, sigma)


def train_ensemble(encoded: List[Tuple[np.ndarray, np.ndarray, np.ndarray]],
                   labels: Dict[str, np.ndarray], n_members: int = 3, epochs: int = 14,
                   batch_size: int = 128, lr: float = 0.006, log=print) -> Ensemble:
    heads_ids = [e[0] for e in encoded]
    all_ids = [e[1] for e in encoded]
    struct = np.stack([e[2] for e in encoded])
    mu = struct.mean(axis=0)
    sigma = struct.std(axis=0) + 1e-3
    s = ((struct - mu) / sigma).astype(np.float32)
    n = len(encoded)

    members = []
    for k in range(n_members):
        net = BagNet(s.shape[1], seed=1000 + k)
        opt = _Adam(lr)
        rng = np.random.default_rng(7 + k)
        for ep in range(epochs):
            order = rng.permutation(n)
            total = 0.0
            for i in range(0, n, batch_size):
                idx = order[i:i + batch_size]
                batch = ([heads_ids[j] for j in idx], [all_ids[j] for j in idx], s[idx],
                         {h: labels[h][idx] for h in HEADS})
                total += net.train_step(batch, opt, smoothing=0.02, dropout=0.25, wd=1e-4) * len(idx)
            opt.lr = lr * (0.5 * (1 + np.cos(np.pi * (ep + 1) / epochs)))
            if log and (ep % 7 == 6 or ep == epochs - 1):
                log(f"  [brain] member {k + 1}/{n_members} epoch {ep + 1}/{epochs} loss={total / n:.4f}")
        members.append(net)
    return Ensemble(members, mu, sigma)
