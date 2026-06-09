import numpy as np
from sklearn.datasets import fetch_openml

mnist = fetch_openml('mnist_784', version=1)
X = mnist.data.values / 255.0
y = mnist.target.values.astype(int)

X_train, X_test = X[:60000], X[60000:]
y_train, y_test = y[:60000], y[60000:]

def one_hot_encode(Y):
    one_hot = np.zeros((Y.size, Y.max() + 1))
    one_hot[np.arange(Y.size), Y] = 1
    return one_hot.T

W1 = np.random.rand(128, 784) - 0.5
b1 = np.random.rand(128, 1) - 0.5
W2 = np.random.rand(10, 128) - 0.5
b2 = np.random.rand(10, 1) - 0.5

X_train = X_train.T
Y_train = one_hot_encode(y_train)

epochs = 500
alpha = 0.1
m = Y_train.shape[1]

for i in range(epochs):
    Z1 = W1.dot(X_train) + b1
    A1 = np.maximum(Z1, 0)
    Z2 = W2.dot(A1) + b2
    A2 = np.exp(Z2) / sum(np.exp(Z2))

    dZ2 = A2 - Y_train
    dW2 = 1 / m * dZ2.dot(A1.T)
    db2 = 1 / m * np.sum(dZ2, axis=1, keepdims=True)
    dZ1 = W2.T.dot(dZ2) * (Z1 > 0)
    dW1 = 1 / m * dZ1.dot(X_train.T)
    db1 = 1 / m * np.sum(dZ1, axis=1, keepdims=True)

    W1 = W1 - alpha * dW1
    b1 = b1 - alpha * db1
    W2 = W2 - alpha * dW2
    b2 = b2 - alpha * db2

    if i % 10 == 0:
        print(f"Epoch {i} completed...")

Z1_test = W1.dot(X_test.T) + b1
A1_test = np.maximum(Z1_test, 0)
Z2_test = W2.dot(A1_test) + b2
A2_test = np.exp(Z2_test) / sum(np.exp(Z2_test))
predictions = np.argmax(A2_test, 0)

accuracy = np.sum(predictions == y_test) / y_test.size
print(accuracy)