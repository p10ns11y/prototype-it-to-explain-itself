#!/usr/bin/env python3
"""
Tiny LLM Prototype: Character-Level LSTM Language Model
=======================================================
This is a complete, runnable prototype to understand how LLMs work under the hood.

CORE CONCEPT:
LLMs are essentially very sophisticated "next-token predictors".
They are trained to answer: "Given this sequence of tokens, what is the most likely next token?"

This prototype demonstrates the full pipeline:
1. Tokenization (character level - simplest to understand)
2. Embedding (turning tokens into learned vectors)
3. Recurrent processing with LSTM (memory / context)
4. Prediction head (logits -> probabilities over vocabulary)
5. Autoregressive generation (feed prediction back as input -> repeat)

Real modern LLMs (GPT, Grok, Claude, Llama...) use:
- Subword tokenization (BPE) instead of characters (larger vocab, ~30k-100k tokens)
- Transformer architecture with self-attention instead of LSTM
- Billions to trillions of parameters
- Trained on internet-scale data for many epochs

But the fundamental loop is IDENTICAL: predict next token, append, repeat.

Run this script to train a tiny model on a story, then generate new text!
You can modify the CORPUS, hyperparameters, or prompt to experiment.

Usage examples:
    python simple_llm_prototype.py
    python simple_llm_prototype.py --prompt "Elara dreamed of" --tokens 200 --temp 0.6
    python simple_llm_prototype.py --show-probs
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import argparse
import sys

# ============================================================
# 1. THE CORPUS (Training Data)
# ============================================================
# In real LLMs this would be terabytes of text (books, web, code...).
# Here we use a short original story repeated so the tiny model can learn patterns.
# The model will overfit (memorize style) which is perfect for a demo.

STORY = """In a quiet village nestled between mountains and a sparkling river, there lived a young inventor named Elara. Elara spent her days tinkering with gears, springs, and strange glowing crystals she found in the forest. She dreamed of building a machine that could talk to the stars. One stormy night, lightning struck her workshop. When the smoke cleared, her machine blinked to life and whispered secrets of the universe. Elara listened in wonder. From that day on, she and the machine explored the mysteries of language, numbers, and dreams together. The villagers called it magic, but Elara knew it was science and curiosity combined."""

CORPUS = (STORY + "\n\n") * 15   # Repeat enough times for the model to learn

# ============================================================
# 2. TOKENIZATION (Character Level)
# ============================================================
# Every LLM starts by converting text into numbers (tokens).
# Character level is the easiest to visualize and debug.
# Real LLMs use subword tokenizers (tiktoken, sentencepiece) for efficiency.

chars = sorted(list(set(CORPUS)))
vocab_size = len(chars)
char2idx = {ch: i for i, ch in enumerate(chars)}
idx2char = {i: ch for i, ch in enumerate(chars)}

def encode(text: str) -> torch.Tensor:
    """Convert string to tensor of integer token IDs."""
    return torch.tensor([char2idx[ch] for ch in text if ch in char2idx], dtype=torch.long)

def decode(ids) -> str:
    """Convert tensor/list of IDs back to readable text."""
    return ''.join([idx2char[int(i)] for i in ids])

print(f"Vocabulary size: {vocab_size} unique characters")
print(f"Characters: {''.join(chars)}\n")

# ============================================================
# 3. DATASET for Training
# ============================================================
# We create many (input_sequence, next_character) pairs by sliding a window over the corpus.
# This teaches the model: "when you see THIS pattern, the next char is usually THAT".

class CharDataset(Dataset):
    def __init__(self, data: torch.Tensor, seq_len: int = 30):
        self.data = data
        self.seq_len = seq_len

    def __len__(self):
        return len(self.data) - self.seq_len - 1

    def __getitem__(self, idx):
        # Input: 30 characters
        x = self.data[idx : idx + self.seq_len]
        # Target: the single character that comes immediately after
        y = self.data[idx + self.seq_len]
        return x, y

# ============================================================
# 4. THE MODEL - Tiny "LLM"
# ============================================================
class TinyLLM(nn.Module):
    """
    A minimal autoregressive language model using LSTM.
    
    Architecture:
        Input IDs -> Embedding (dense vectors) -> LSTM (recurrent memory) -> Linear (prediction head)
    
    Why LSTM?
    - Maintains a hidden state that acts as "memory" or "context" across time steps.
    - Simple to understand compared to full Transformer.
    
    In real LLMs the LSTM is replaced by stacked Transformer decoder blocks
    with multi-head self-attention, which allows parallel processing and much better
    long-range dependencies.
    """
    def __init__(self, vocab_size: int, embed_dim: int = 64, hidden_dim: int = 128, num_layers: int = 2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.25 if num_layers > 1 else 0.0
        )
        self.head = nn.Linear(hidden_dim, vocab_size)  # Predicts logits over entire vocabulary
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

    def forward(self, x: torch.Tensor, hidden=None):
        """
        x shape: (batch_size, seq_len)
        Returns: logits (batch_size, seq_len, vocab_size), hidden state
        """
        emb = self.embed(x)                    # (B, T, embed_dim)
        out, hidden = self.lstm(emb, hidden)   # (B, T, hidden_dim)
        logits = self.head(out)                # (B, T, vocab_size)
        return logits, hidden

    def init_hidden(self, batch_size: int, device: str):
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        c0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        return (h0, c0)

# ============================================================
# 5. TRAINING LOOP
# ============================================================
def train_model(model: TinyLLM, dataloader: DataLoader, epochs: int = 25, lr: float = 0.004, device: str = 'cpu'):
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    
    print("=== Training Tiny LLM ===")
    print(f"Epochs: {epochs} | Learning rate: {lr} | Device: {device}\n")
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0.0
        for batch_x, batch_y in dataloader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            
            optimizer.zero_grad()
            
            logits, _ = model(batch_x)           # (B, T, V)
            # We only care about predicting the token RIGHT AFTER the input sequence
            last_step_logits = logits[:, -1, :]  # (B, V)
            
            loss = criterion(last_step_logits, batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # stabilize training
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            avg_loss = total_loss / len(dataloader)
            print(f"Epoch {epoch+1:3d}/{epochs}  |  Loss: {avg_loss:.4f}")
    
    print("\nTraining finished! The model has internalized patterns from the story.\n")
    return model

# ============================================================
# 6. TEXT GENERATION (Autoregressive Decoding)
# ============================================================
def generate_text(model: TinyLLM, seed_text: str, max_new_tokens: int = 150, 
                  temperature: float = 0.8, device: str = 'cpu') -> str:
    """
    The heart of how every modern LLM generates text:
    1. Encode current context
    2. Predict probability distribution over next token
    3. Sample one token from that distribution
    4. Append it to context
    5. Repeat until desired length
    
    Temperature controls randomness:
        < 0.5  -> more deterministic / repetitive
        ~ 0.7-0.9 -> balanced creativity
        > 1.5  -> more chaotic / nonsensical
    """
    model.eval()
    model = model.to(device)
    
    # Start with the seed
    context = encode(seed_text).unsqueeze(0).to(device)  # shape (1, current_length)
    generated_ids = list(context[0].cpu().numpy())
    
    hidden = None
    seq_window = 40  # how much context to feed each step (LSTM memory helps anyway)
    
    with torch.no_grad():
        for _ in range(max_new_tokens):
            # Feed recent context (prevents very long sequences)
            input_seq = context[:, -seq_window:] if context.size(1) > seq_window else context
            
            logits, hidden = model(input_seq, hidden)
            
            # Get logits for the very next position
            next_logits = logits[0, -1, :] / max(temperature, 1e-6)
            
            # Convert to probabilities
            probs = torch.softmax(next_logits, dim=-1)
            
            # Sample from the distribution (this is where "creativity" comes from)
            next_id = torch.multinomial(probs, num_samples=1).item()
            
            generated_ids.append(next_id)
            
            # Append to growing context
            context = torch.cat([context, torch.tensor([[next_id]], device=device)], dim=1)
    
    return decode(generated_ids)

def show_top_predictions(model: TinyLLM, context_text: str, top_k: int = 6, 
                         temperature: float = 1.0, device: str = 'cpu'):
    """Visualize the probability distribution the model assigns to possible next characters.
    This is what 'understanding' looks like inside an LLM."""
    model.eval()
    ctx = encode(context_text).unsqueeze(0).to(device)
    
    with torch.no_grad():
        logits, _ = model(ctx)
        next_logits = logits[0, -1, :] / max(temperature, 1e-6)
        probs = torch.softmax(next_logits, dim=-1)
        
        top_p, top_idx = torch.topk(probs, top_k)
        
        print(f"\nContext ending with: ...'{context_text[-50:]}'")
        print("Model's belief about what comes next:")
        for rank, (prob, idx) in enumerate(zip(top_p.tolist(), top_idx.tolist()), 1):
            char = idx2char[idx]
            display = repr(char) if char in [' ', '\n', '\t'] else f"'{char}'"
            print(f"  {rank}. {display:6s}  →  {prob*100:5.1f}% probability")

# ============================================================
# 7. MAIN ENTRY POINT
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Interactive Tiny LLM Prototype - Understand how LLMs really work",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_llm_prototype.py
  python simple_llm_prototype.py --prompt "Elara and the machine" --tokens 180 --temp 0.65
  python simple_llm_prototype.py --show-probs --prompt "She dreamed of building"
        """
    )
    parser.add_argument("--prompt", type=str, default="In a quiet village", 
                        help="Starting prompt / seed text for generation")
    parser.add_argument("--tokens", type=int, default=140, 
                        help="Number of new characters/tokens to generate")
    parser.add_argument("--temp", type=float, default=0.75, 
                        help="Sampling temperature (0.1=safe, 1.5=wild)")
    parser.add_argument("--show-probs", action="store_true",
                        help="After generation, show what the model thinks should come next")
    parser.add_argument("--epochs", type=int, default=25, help="Training epochs (more = better fit on small data, 25 is good for quick demo)")
    
    args = parser.parse_args()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Device: {device}  |  PyTorch: {torch.__version__}\n")
    
    # --- Data Preparation ---
    data_tensor = encode(CORPUS)
    print(f"Corpus size: {len(CORPUS):,} characters  →  {len(data_tensor):,} tokens")
    
    seq_len = 30
    dataset = CharDataset(data_tensor, seq_len=seq_len)
    dataloader = DataLoader(dataset, batch_size=48, shuffle=True, drop_last=True)
    print(f"Training examples created: {len(dataset):,}\n")
    
    # --- Model ---
    model = TinyLLM(vocab_size, embed_dim=64, hidden_dim=128, num_layers=2)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model created with {total_params:,} trainable parameters")
    print("   (Real LLMs have 1B - 1T+ parameters)\n")
    
    # --- Train ---
    model = train_model(model, dataloader, epochs=args.epochs, lr=0.0035, device=device)
    
    # --- Generate ---
    print("=" * 65)
    print("GENERATION DEMO")
    print("=" * 65)
    
    seed = args.prompt
    print(f"\nYour prompt: \"{seed}\"")
    print("-" * 65)
    
    generated = generate_text(model, seed, max_new_tokens=args.tokens, 
                              temperature=args.temp, device=device)
    print(generated)
    print("-" * 65)
    
    if args.show_probs:
        show_top_predictions(model, seed, top_k=7, temperature=1.0, device=device)
    
    # --- Educational note ---
    print("\n" + "=" * 65)
    print("WHAT YOU JUST SAW:")
    print("=" * 65)
    print("""
1. The model learned statistical patterns from the story (Elara, village, machine, stars, etc.).
2. Generation is purely autoregressive: each new character is chosen based on what came before.
3. Temperature controls how "creative" vs "safe" the sampling is.
4. Because the corpus is tiny, the model mostly reproduces similar sentences and style.
   In real LLMs the training data is so vast that it generalizes to almost any topic.

Try these experiments to deepen understanding:
- Change the STORY in the code and retrain
- Increase --epochs or hidden_dim
- Try different --temp values (0.3 vs 1.2)
- Use --show-probs to peek inside the model's "mind" at prediction time
- Add more layers or switch to a Transformer (advanced)

This is the same fundamental mechanism that powers Grok, GPT-4, Claude, and Llama.
The magic is in the scale + clever architecture (Transformers) + massive data.
""")

if __name__ == "__main__":
    main()
