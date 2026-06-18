
# 👋 Welcomeeee!!! 👋
**Week 5** You're finally going past "neighbors talking to neighbors" and into *why* the GCN equation looks the way it does. 🚀
I low-key hope the math humbles you a little this week — that's the whole point. 💪🔥
---
## 📚 Reading Time 📖
* 📘 **The Core Mission:** [Kipf's GCN Blog Post](https://tkipf.github.io/graph-convolutional-networks/) first — pure intuition, no scary symbols yet. 🧠
* 🏋️ **The Real Boss Fight:** [Kipf & Welling, ICLR 2017](https://arxiv.org/pdf/1609.02907) — **Section 2 only**, but read it *slow*. This is where last week's aggregation formula gets a proof of identity.
* 🌌 **For the Hardworkers:** [Understanding Convolutions on Graphs (Distill.pub)](https://distill.pub/2021/understanding-gnns/) — gorgeous interactive bridge between image conv and graph conv. Optional, but you'll thank yourself later.

<!--
  Me reading "first-order Chebyshev approximation" for the first time:
  [ Meme Idea: Spongebob staring into the camera in horror ]
-->

---
## 🎥 If Reading Isn't Hitting, Watch These 📺
* 🎓 **The Lifeline:** [CS224W Playlist](https://www.youtube.com/playlist?list=PLoROMvodv4rPLKxIpqhjhPgdQy7imNkDn) — the exact same derivation, walked through slower, with diagrams.
* 🔬 **Paper, but Spoken Aloud:** [Graph Convolutional Networks (GCN) | GNN Paper Explained — AI Epiphany](https://www.youtube.com/watch?v=VyIOfIglrUM) — a 44-min line-by-line walk through the same paper you're reading. Great for confirming you got the derivation right.
* 🧊 **For the Hardworkers (bonus, ties into Q4):** [Understanding Oversmoothing in GNNs — Google Algorithms Seminar](https://www.youtube.com/watch?v=MLiEoJOhXJA) — a research talk on *why* deep GCNs collapse. Not required, but good if the oversmoothing question hooks you.

---
## 💻 The Coding Playground: Same PyG, New Tricks 🧪
Open `notebooks/GCN_Oversmoothing_Starter.ipynb`. You'll be:
- Hand-building the normalized adjacency matrix (yes, with self-loops 👀)
- Writing a GCN layer in raw NumPy before PyG does it for you
- Watching a GCN literally get *worse* the deeper you stack it (over-smoothing is real, and you'll see it happen)

---
## 🎯 The Philosophy for the Week
Four questions. Easy → Medium. No 10-page proofs this time, promise. 🙏
📢 **Remember:** I don't care how fast you finish — I care whether you can explain *why* the self-loop matters in one sentence to a confused friend. 💯✨

Let's get after it! 🦾🕸️
