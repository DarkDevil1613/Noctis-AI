import os
import json
import numpy as np
import onnxruntime as ort
from pathlib import Path
from datetime import datetime

BASE_DIR     = Path(__file__).resolve().parent.parent
ONLINE_PATH  = Path("N:/memory/vectors")
OFFLINE_PATH = BASE_DIR / "logs" / "offline_cache" / "vectors"

MODEL_PATH   = BASE_DIR / "memory" / "onnx_model"

# ── ONNX Embedding Model ────────────────────────────────────────────────────
# Uses the same ONNXMiniLM_L6_V2 model chromadb bundles internally
# We download it once from huggingface and cache it locally

TOKENIZER_URL = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/tokenizer.json"
MODEL_URL     = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx"
VOCAB_URL     = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/vocab.txt"

def _download_model():
    """Download ONNX model files if not present."""
    import urllib.request
    MODEL_PATH.mkdir(parents=True, exist_ok=True)

    files = {
        MODEL_PATH / "tokenizer.json": TOKENIZER_URL,
        MODEL_PATH / "model.onnx":     MODEL_URL,
        MODEL_PATH / "vocab.txt":      VOCAB_URL,
    }

    for dest, url in files.items():
        if not dest.exists():
            print(f"[VectorStore] Downloading {dest.name}...")
            urllib.request.urlretrieve(url, dest)
            print(f"[VectorStore] {dest.name} ready.")

# ── Tokenizer (pure Python, no transformers needed) ─────────────────────────
class SimpleTokenizer:
    """Minimal WordPiece tokenizer for MiniLM — no transformers dependency."""

    def __init__(self, vocab_path: Path):
        self.vocab = {}
        self.ids_to_tokens = {}
        with open(vocab_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                token = line.strip()
                self.vocab[token] = idx
                self.ids_to_tokens[idx] = token

        self.unk_id = self.vocab.get("[UNK]", 0)
        self.cls_id = self.vocab.get("[CLS]", 101)
        self.sep_id = self.vocab.get("[SEP]", 102)
        self.pad_id = self.vocab.get("[PAD]", 0)
        self.max_len = 128

    def _tokenize_word(self, word: str):
        if word in self.vocab:
            return [word]
        tokens = []
        start = 0
        while start < len(word):
            end = len(word)
            found = None
            while start < end:
                substr = word[start:end]
                if start > 0:
                    substr = "##" + substr
                if substr in self.vocab:
                    found = substr
                    break
                end -= 1
            if found is None:
                tokens.append("[UNK]")
                break
            tokens.append(found)
            start = end - (2 if start > 0 else 0) + len(found.lstrip("##"))
            start = end
        return tokens if tokens else ["[UNK]"]

    def encode(self, text: str):
        text = text.lower().strip()
        words = text.split()
        tokens = ["[CLS]"]
        for word in words:
            tokens.extend(self._tokenize_word(word))
        tokens.append("[SEP]")

        # Truncate
        if len(tokens) > self.max_len:
            tokens = tokens[:self.max_len - 1] + ["[SEP]"]

        ids = [self.vocab.get(t, self.unk_id) for t in tokens]
        mask = [1] * len(ids)

        # Pad
        pad_len = self.max_len - len(ids)
        ids  += [self.pad_id] * pad_len
        mask += [0] * pad_len
        type_ids = [0] * self.max_len

        return ids, mask, type_ids


# ── Embedder ────────────────────────────────────────────────────────────────
class ONNXEmbedder:
    def __init__(self):
        _download_model()
        self.tokenizer = SimpleTokenizer(MODEL_PATH / "vocab.txt")
        self.session = ort.InferenceSession(
            str(MODEL_PATH / "model.onnx"),
            providers=["CPUExecutionProvider"]
        )

    def _mean_pool(self, token_embeddings: np.ndarray, mask: np.ndarray) -> np.ndarray:
        mask_expanded = mask[:, :, np.newaxis].astype(np.float32)
        summed = (token_embeddings * mask_expanded).sum(axis=1)
        counts = mask_expanded.sum(axis=1).clip(min=1e-9)
        return summed / counts

    def embed(self, texts: list[str]) -> np.ndarray:
        all_ids, all_masks, all_types = [], [], []
        for text in texts:
            ids, mask, types = self.tokenizer.encode(text)
            all_ids.append(ids)
            all_masks.append(mask)
            all_types.append(types)

        input_ids      = np.array(all_ids,   dtype=np.int64)
        attention_mask = np.array(all_masks, dtype=np.int64)
        token_type_ids = np.array(all_types, dtype=np.int64)

        outputs = self.session.run(None, {
            "input_ids":      input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        })

        embeddings = self._mean_pool(outputs[0], attention_mask)

        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True).clip(min=1e-9)
        return embeddings / norms


# ── Vector Store ─────────────────────────────────────────────────────────────
class NoctisVectorStore:
    def __init__(self):
        self.embedder = None  # lazy init
        self._online = False
        self._path = self._resolve_path()
        self._vectors_file  = self._path / "vectors.npy"
        self._metadata_file = self._path / "metadata.json"
        self._vectors:  np.ndarray = None
        self._metadata: list[dict] = []
        self._load()

    def _resolve_path(self) -> Path:
        try:
            if ONLINE_PATH.exists():
                test = ONLINE_PATH / ".write_test"
                test.write_text("ok")
                test.unlink()
                self._online = True
                print("[VectorStore] Memory Server Online (N:\\memory\\vectors)")
                return ONLINE_PATH
        except Exception:
            pass

        self._online = False
        OFFLINE_PATH.mkdir(parents=True, exist_ok=True)
        print("[VectorStore] Storage: Local Vector Store")
        return OFFLINE_PATH

    def _load(self):
        if self._vectors_file.exists():
            self._vectors = np.load(str(self._vectors_file))
        if self._metadata_file.exists():
            with open(self._metadata_file, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)
        print(f"[VectorStore] Loaded {len(self._metadata)} entries.")

    def _save(self):
        if self._vectors is not None:
            np.save(str(self._vectors_file), self._vectors)
        with open(self._metadata_file, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2)

    def _get_embedder(self) -> ONNXEmbedder:
        if self.embedder is None:
            print("[VectorStore] Loading ONNX embedder...")
            self.embedder = ONNXEmbedder()
            print("[VectorStore] Embedder ready.")
        return self.embedder

    def add(self, text: str, metadata: dict = None):
        """Add a text entry with optional metadata."""
        embedder = self._get_embedder()
        vec = embedder.embed([text])[0]  # shape (384,)

        if self._vectors is None:
            self._vectors = vec[np.newaxis, :]
        else:
            self._vectors = np.vstack([self._vectors, vec[np.newaxis, :]])

        entry = {
            "text":      text,
            "timestamp": datetime.now().isoformat(),
            "metadata":  metadata or {}
        }
        self._metadata.append(entry)
        self._save()

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Return top_k most similar entries to query."""
        if self._vectors is None or len(self._metadata) == 0:
            return []

        embedder = self._get_embedder()
        q_vec = embedder.embed([query])[0]

        # Cosine similarity (vectors already L2-normalized)
        scores = self._vectors @ q_vec
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                "text":      self._metadata[idx]["text"],
                "score":     float(scores[idx]),
                "timestamp": self._metadata[idx]["timestamp"],
                "metadata":  self._metadata[idx]["metadata"],
            })
        return results

    def build_context(self, query: str, top_k: int = 5) -> str:
        """Build a context string to inject into system prompt."""
        results = self.search(query, top_k=top_k)
        if not results:
            return ""
        lines = ["[Memory Context]"]
        for r in results:
            lines.append(f"- {r['text']} (score: {r['score']:.2f})")
        return "\n".join(lines)

    def count(self) -> int:
        return len(self._metadata)

    def sync_offline_cache(self):
        """Merge offline vectors into online store when server comes back."""
        if not self._online:
            return
        offline_meta = OFFLINE_PATH / "metadata.json"
        offline_vecs = OFFLINE_PATH / "vectors.npy"
        if not offline_meta.exists():
            return

        print("[VectorStore] Syncing offline cache to server...")
        with open(offline_meta, "r", encoding="utf-8") as f:
            o_meta = json.load(f)
        o_vecs = np.load(str(offline_vecs)) if offline_vecs.exists() else None

        if o_vecs is None or len(o_meta) == 0:
            return

        for i, entry in enumerate(o_meta):
            vec = o_vecs[i]
            if self._vectors is None:
                self._vectors = vec[np.newaxis, :]
            else:
                self._vectors = np.vstack([self._vectors, vec[np.newaxis, :]])
            self._metadata.append(entry)

        self._save()
        # Clear offline cache
        offline_meta.unlink()
        offline_vecs.unlink()
        print(f"[VectorStore] Synced {len(o_meta)} offline entries.")