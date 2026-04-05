import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Input

input_layer = Input(shape=(3,))

# Encoder
h1 = Dense(32, activation='relu')(input_layer)
h2 = Dense(16, activation='relu')(h1)
h3 = Dense(8, activation='relu')(h2)

# Embedding (2D)
embedding = Dense(2, activation='linear', name="embedding_layer")(h3)

# Decoder
d1 = Dense(8, activation='relu')(embedding)
d2 = Dense(16, activation='relu')(d1)
output_layer = Dense(3, activation='linear')(d2)

model = Model(inputs=input_layer, outputs=output_layer)
model.compile(optimizer='adam', loss='mse')
