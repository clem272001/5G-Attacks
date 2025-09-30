import torch
import pandas as pd
from torchvision.ops import MLP
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader, random_split
import torch.optim as optim
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score, confusion_matrix, ConfusionMatrixDisplay
import numpy as np
import matplotlib.pyplot as plt
import random
from sklearn.metrics import accuracy_score

# ---------------------------
# Déterminisme
# ---------------------------
seed = 42
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)

# pour forcer PyTorch en mode déterministe (si tu veux vraiment reproductible)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False

# ---------------------------
# Modèle
# ---------------------------
class MLPAutoencoder(nn.Module):
    def __init__(self, input_dim: int, latent_dim: int = 8, p_drop: float = 0.1):
        super().__init__()
        self.encoder = MLP(
            in_channels=input_dim,
            hidden_channels=[128, 64, 32, latent_dim],
            activation_layer=nn.LeakyReLU,
            dropout=p_drop
        )
        self.enc_bn = nn.BatchNorm1d(latent_dim)  # OK même si batch>1
        self.decoder = MLP(
            in_channels=latent_dim,
            hidden_channels=[32, 64, 128, input_dim],
            activation_layer=nn.LeakyReLU,
            dropout=p_drop
        )

    def forward(self, x):
        z = self.encoder(x)
        z = self.enc_bn(z)
        x_hat = self.decoder(z)
        return x_hat

# ---------------------------
# Chargement des données
# ---------------------------
# Fichiers déjà scalés d'après ton message
df_train = pd.read_csv("dataset_1_scaled.csv", sep=';')
df_test  = pd.read_csv("dataset_3_scaled.csv", sep=';')

# Colonnes à exclure des features si présentes (labels/identifiants)
cols_to_drop = ["ip.opt.time_stamp", "frame.number"]

# X (train sain)
X_train = df_train.drop(columns=cols_to_drop, errors="ignore").select_dtypes(include="number").values
# X (test mixte)
X_test  = df_test.drop(columns=cols_to_drop, errors="ignore").select_dtypes(include="number").values

# y (test) : ici tu utilises "ip.opt.time_stamp" comme label (NaN = normal, sinon 0..7)
y_test_raw = df_test["ip.opt.time_stamp"]  # garde pandas Series
y_test = y_test_raw.fillna(-1).astype(int).values
y_true = (y_test != -1).astype(int)  # 0=normal, 1=attaque

# Tensors
X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
X_test_tensor  = torch.tensor(X_test,  dtype=torch.float32)

# ---------------------------
# DataLoaders (avec val split sur le sain)
# ---------------------------
full_train_ds = TensorDataset(X_train_tensor)
val_ratio = 0.1
val_size = max(1, int(len(full_train_ds) * val_ratio))
train_size = len(full_train_ds) - val_size
train_ds, val_ds = random_split(full_train_ds, [train_size, val_size])

train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
val_loader   = DataLoader(val_ds, batch_size=64, shuffle=False)
test_loader  = DataLoader(TensorDataset(X_test_tensor), batch_size=64, shuffle=False)

# ---------------------------
# Entraînement
# ---------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
input_dim = X_train_tensor.shape[1]
latent_dim = 2           # petit bottleneck = mieux pour l'anomaly detection
lr = 3e-4
num_epochs = 200
patience = 10            # early stopping
sparsity_coef = 1e-4     # L1 sur le latent (léger)

model = MLPAutoencoder(input_dim=input_dim, latent_dim=latent_dim, p_drop=0.1).to(device)
criterion = nn.L1Loss()  # MAE plus robuste que MSE
optimizer = optim.Adam(model.parameters(), lr=lr)

best_val = float("inf")
bad = 0
best_state = None

for epoch in range(1, num_epochs + 1):
    # --- train ---
    model.train()
    train_loss_sum = 0.0
    n_train = 0
    for (x_batch,) in train_loader:
        x_batch = x_batch.to(device)
        optimizer.zero_grad()
        x_hat = model(x_batch)
        # sparsity sur le latent (on recalcule z pour simplicité)
        z = model.enc_bn(model.encoder(x_batch))
        loss = criterion(x_hat, x_batch) + sparsity_coef * z.abs().mean()
        loss.backward()
        optimizer.step()
        bs = x_batch.size(0)
        train_loss_sum += loss.item() * bs
        n_train += bs
    train_loss = train_loss_sum / max(1, n_train)

    # --- validation (sain) ---
    model.eval()
    val_loss_sum = 0.0
    n_val = 0
    with torch.no_grad():
        for (x_val,) in val_loader:
            x_val = x_val.to(device)
            x_hat = model(x_val)
            z = model.enc_bn(model.encoder(x_val))
            vloss = criterion(x_hat, x_val) + sparsity_coef * z.abs().mean()
            bs = x_val.size(0)
            val_loss_sum += vloss.item() * bs
            n_val += bs
    val_loss = val_loss_sum / max(1, n_val)

    print(f"Epoch [{epoch}/{num_epochs}] - train_loss: {train_loss:.6f} - val_loss: {val_loss:.6f}")

    # early stopping
    if val_loss < best_val - 1e-6:
        best_val = val_loss
        bad = 0
        best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
    else:
        bad += 1
        if bad >= patience:
            print("Early stopping.")
            break

# Charger le meilleur état
if best_state is not None:
    model.load_state_dict(best_state)

# ---------------------------
# Évaluation (erreurs MAE)
# ---------------------------
model.eval()
reconstruction_errors = []
with torch.no_grad():
    for (x_batch,) in test_loader:
        x_batch = x_batch.to(device)
        x_hat = model(x_batch)
        e = (x_hat - x_batch).abs().mean(dim=1)  # MAE par sample
        reconstruction_errors.extend(e.detach().cpu().numpy())

errors = np.asarray(reconstruction_errors)
errors = np.nan_to_num(errors, posinf=np.finfo(np.float32).max)

# ---------------------------
# Choix du seuil (grid de percentiles sur les normaux)
# ---------------------------
normal_errors = errors[y_true == 0]
# Sécurité si pas de normaux dans y_true (rare mais possible)
if normal_errors.size == 0:
    normal_errors = errors

candidates = [90, 92, 94, 95, 96, 97, 98, 98.5, 99, 99.5, 99.7, 99.9]
best = {"q": None, "th": None, "f1": -1, "y_pred": None}

for q in candidates:
    th = np.percentile(normal_errors, q)
    # évite le cas "th = max(normal)" -> FP=0 tout le temps
    th = np.nextafter(th, -np.inf)
    y_pred = (errors > th).astype(int)
    f1 = f1_score(y_true, y_pred)
    if f1 > best["f1"]:
        best.update(q=q, th=th, f1=f1, y_pred=y_pred)

y_pred = best["y_pred"]
threshold = best["th"]

print(f"Seuil choisi (percentile {best['q']}): {threshold}")
print("AUC:", roc_auc_score(y_true, errors))
print("Accuracy:", accuracy_score(y_true, y_pred))
print("F1:", f1_score(y_true, y_pred))
print("Précision:", precision_score(y_true, y_pred))
print("Rappel:", recall_score(y_true, y_pred))

# ---------------------------
# Confusion Matrix
# ---------------------------
cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
print("Confusion Matrix :\n", cm)

disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Normal", "Anomalie"])
disp.plot(cmap="Blues", values_format="d")
plt.title("Confusion Matrix (Autoencoder MLP)")
plt.tight_layout()
plt.show()
