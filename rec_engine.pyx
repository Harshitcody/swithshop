# rec_engine.pyx
from libc.stdlib cimport malloc, free
cimport cython
import math
from collections import defaultdict

cdef class RecEngine:
    cdef public list products
    cdef dict _vocab_index
    cdef list _doc_vectors
    cdef dict _idf
    cdef int vocab_size
    cdef dict user_pref
    cdef set liked_ids
    cdef int n_products

    def __cinit__(self):
        self.products = []
        self._vocab_index = {}
        self._doc_vectors = []
        self._idf = {}
        self.vocab_size = 0
        self.user_pref = {}
        self.liked_ids = set()
        self.n_products = 0

    cpdef add_product(self, int prod_id, title, desc, img=""):
        """Add product with optional image."""
        self.products.append({
            "id": prod_id,
            "title": title or "",
            "desc": desc or "",
            "img": img or ""
        })

    cpdef build(self):
        """Build vocabulary, compute TF-IDF, normalize."""
        cdef int i, tid
        cdef dict df = {}
        cdef list tokenized_docs = []
        vid = 0
        for prod in self.products:
            text = (prod["title"] + " " + prod["desc"]).lower()
            toks = _tokenize(text)
            tokenized_docs.append(toks)
            seen = set()
            for t in toks:
                if t not in self._vocab_index:
                    self._vocab_index[t] = vid
                    vid += 1
                if t not in seen:
                    seen.add(t)
                    df[self._vocab_index[t]] = df.get(self._vocab_index[t], 0) + 1
        self.vocab_size = vid
        self.n_products = len(self.products)
        N = float(self.n_products) if self.n_products > 0 else 1.0
        for term_id, cnt in df.items():
            self._idf[term_id] = math.log((N + 1.0) / (cnt + 1.0)) + 1.0
        self._doc_vectors = []
        for toks in tokenized_docs:
            tf = {}
            for t in toks:
                tid = self._vocab_index[t]
                tf[tid] = tf.get(tid, 0.0) + 1.0
            vec = {}
            cdef double norm = 0.0
            for tid, tfval in tf.items():
                val = tfval * self._idf.get(tid, 0.0)
                vec[tid] = val
                norm += val * val
            if norm > 0:
                norm = math.sqrt(norm)
                for tid in list(vec.keys()):
                    vec[tid] = vec[tid] / norm
            self._doc_vectors.append(vec)
        self.user_pref = {}
        self.liked_ids = set()

    cpdef like_product(self, int prod_id):
        cdef int idx = _find_product_index(self, prod_id)
        if idx == -1:
            raise ValueError(f"product id {prod_id} not found")
        self.liked_ids.add(prod_id)
        doc_vec = self._doc_vectors[idx]
        for tid, val in doc_vec.items():
            self.user_pref[tid] = self.user_pref.get(tid, 0.0) + val
        cdef double norm = 0.0
        for v in self.user_pref.values():
            norm += v * v
        if norm > 0:
            norm = math.sqrt(norm)
            for tid in list(self.user_pref.keys()):
                self.user_pref[tid] = self.user_pref[tid] / norm

    cpdef list get_recommendations(self, int top_n=5, exclude_liked=True):
        if not self.user_pref:
            return []
        scores = []
        for i in range(self.n_products):
            pid = self.products[i]["id"]
            if exclude_liked and pid in self.liked_ids:
                continue
            sim = _sparse_cosine_sim(self.user_pref, self._doc_vectors[i])
            scores.append((sim, i))
        scores.sort(key=lambda x: -x[0])
        res = []
        take = top_n if top_n < len(scores) else len(scores)
        for j in range(take):
            idx = scores[j][1]
            prod = self.products[idx]
            res.append({
                "id": prod["id"],
                "title": prod["title"],
                "desc": prod["desc"],
                "img": prod["img"],
                "score": scores[j][0]
            })
        return res

@cython.boundscheck(False)
@cython.wraparound(False)
cdef list _tokenize(str text):
    cdef list out = []
    cdef list tmp = []
    for ch in text:
        if ch.isalnum():
            tmp.append(ch)
        else:
            if tmp:
                out.append("".join(tmp))
                tmp = []
    if tmp:
        out.append("".join(tmp))
    return out

cdef int _find_product_index(RecEngine self, int prod_id):
    cdef int i
    for i in range(self.n_products):
        if self.products[i]["id"] == prod_id:
            return i
    return -1

cdef double _sparse_cosine_sim(dict a, dict b):
    cdef double s = 0.0
    if len(a) < len(b):
        for tid, val in a.items():
            if tid in b:
                s += val * b[tid]
    else:
        for tid, val in b.items():
            if tid in a:
                s += val * a[tid]
    return s
