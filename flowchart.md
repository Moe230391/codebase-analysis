graph LR

%% ETL Process
subgraph "ETL Process"
A[Crypto Exchange API] --> B[Data Extraction]
B --> C[Data Transformation]
C --> D[Feature Engineering]
D --> E[Historical Data]
end

%% Training Phase
subgraph "Training Phase"
E --> F[Transformer Model Training]
F --> G[Trained Transformer Model]
E --> H[RL Environment Simulation]
G --> I[State Input]
H --> I
I --> J[RL Agent]
J --> K[Action: Buy/Sell/Hold]
K --> H
H --> L[Reward]
L --> J
end

%% Inference and Trading Phase
subgraph "Inference & Trading"
G --> M[Inference]
M --> N[Trading Decisions]
N --> O[Execution]
O --> P[Market]
end
