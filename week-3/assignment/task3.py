import torch
import torch.nn as nn
import torch.optim as optim

X = torch.linspace(-10, 10, 100).view(-1, 1)
y = X

model = nn.Linear(1, 1)
optimizer = optim.SGD(model.parameters(), lr=0.01)
criterion = nn.MSELoss()

for epoch in range(1000):
    optimizer.zero_grad()
    predictions = model(X)
    loss = criterion(predictions, y)
    loss.backward()
    optimizer.step()

print(model.weight.data)
print(model.bias.data)