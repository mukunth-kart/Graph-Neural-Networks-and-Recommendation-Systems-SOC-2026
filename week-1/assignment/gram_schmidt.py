import numpy as np

def gram_schmidt(A):
    Q = np.zeros_like(A, dtype=float)
    
    for i in range(A.shape[1]):
        v = A[:, i]
        u = np.copy(v)
        
        for j in range(i):
            q_j = Q[:, j]
            u -= (np.dot(v, q_j) / np.dot(q_j, q_j)) * q_j
            
        Q[:, i] = u / np.linalg.norm(u)
        
    return Q

A = np.array([[1.0, 1.0, 0.0],
              [1.0, 3.0, 1.0],
              [2.0, -1.0, 1.0]])

Q = gram_schmidt(A)
print(Q)
print(np.allclose(Q.T @ Q, np.eye(Q.shape[1])))