import numpy as np
import onnxruntime as ort

import os
vad_path = os.path.join(os.path.dirname(__file__), 'silero_vad.onnx')
session = ort.InferenceSession(vad_path)
state = np.zeros((2, 1, 128), dtype=np.float32)
audio = np.zeros(512, dtype=np.float32)
sr = np.array(16000, dtype=np.int64)

inputs = {
    'input': audio[np.newaxis, :],
    'state': state,
    'sr': sr
}
out, new_state = session.run(None, inputs)
print("Speech prob:", out[0][0])
print("State shape:", new_state.shape)
