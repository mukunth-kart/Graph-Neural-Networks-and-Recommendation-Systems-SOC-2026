import torch
import torch.nn as nn
import torch.optim as optim

X = torch.linspace(-10, 10, 100).view(-1, 1)
y = X**2

model = nn.Sequential(
    nn.Linear(1, 10),
    nn.ReLU(),
    nn.Linear(10, 1)
)

optimizer = optim.Adam(model.parameters(), lr=0.01)
criterion = nn.MSELoss()

for epoch in range(2000):
    optimizer.zero_grad()
    predictions = model(X)
    loss = criterion(predictions, y)
    loss.backward()
    optimizer.step()

for name, param in model.named_parameters():
    print(name, param.data)