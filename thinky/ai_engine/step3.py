# ai_engine/step3.py
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input, Dropout, BatchNormalization

# المدخلات: (الدقة، السرعة، الاستقلال، الاستقرار)[cite: 10]
input_layer = Input(shape=(4,))

# Encoder (المشفر)[cite: 10]
x = Dense(64, activation='relu')(input_layer)
x = BatchNormalization()(x)
x = Dropout(0.2)(x) 

x = Dense(32, activation='relu')(x)
x = Dense(16, activation='relu')(x)

# Embedding (2D) - لتمثيل الطالب في فضاء ثنائي الأبعاد[cite: 10]
embedding = Dense(2, activation='linear', name="embedding_layer")(x)

# Decoder (فك التشفير)[cite: 10]
x = Dense(16, activation='relu')(embedding)
x = Dense(32, activation='relu')(x)
output_layer = Dense(4, activation='linear')(x)

model = Model(inputs=input_layer, outputs=output_layer)
model.compile(optimizer='adam', loss='mse')