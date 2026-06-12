import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# caricamento dataset
df = pd.read_csv("dataset.csv", sep=";", decimal=",", engine="python")

print("Shape dataset:", df.shape)
print(df.head())

print("INFO:")
print(df.info())

print("valori mancanti;")
print(df.isna().sum())


# distribuzione
cols_to_plot = [
    "tempForno",
    "deltaT_future",
    "resOutput",
    "errore"
]

df[cols_to_plot].hist(bins=50, figsize=(12, 8))
plt.suptitle("Distribuzione variabili principali", fontsize=16)
plt.show()


# # andamento
# plt.figure(figsize=(15, 6))
# plt.plot(df["tempForno"], label="Temp attuale")
# plt.plot(df["tempForno_future"], label="Temp futura (+x sec)", alpha=0.7)
# plt.title("Andamento temporale temperatura attuale vs futura")
# plt.xlabel("Campioni")
# plt.ylabel("Temperatura [°C]")
# plt.grid(True)
# plt.legend()
# plt.show()


#correlazini
corr_cols=[
    "tempForno",
    "tempRate",
    "resOutput",
    "deltaT_future",
    "power",
    "totalElapsedTime",
    "eco2",
    "tvoc"
]
corr = df[corr_cols].corr()
plt.figure(figsize=(12, 10))
sns.heatmap(corr, cmap="coolwarm", annot=False)
plt.title("Matrice correlazione")
plt.show()


#RELAZIONI
#potenza - temp futura
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x="resOutput", y="tempForno", alpha=0.3)
plt.title("Relazione potenza applicata - temperatura")
plt.grid(True)
plt.show()

#deltaT - potenza
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x="resOutput", y="deltaT_future", alpha=0.3)
plt.title("Relazione potenza applicata - temperatura")
plt.grid(True)
plt.show()

# #potenza - temp futura
# plt.figure(figsize=(10, 6))
# sns.scatterplot(data=df, x="tempForno", y="tempForno_future", alpha=0.3)
# plt.title("Relazione temperatura attuale - temperatura futura")
# plt.grid(True)
# plt.show()

# #potenza - temp futura
# plt.figure(figsize=(10, 6))
# sns.scatterplot(data=df, x="resOutput", y="tempForno_future", alpha=0.3)
# plt.title("Relazione rateo salita - temperatura futura")
# plt.grid(True)
# plt.show()


#BOXPLOT
#box plot per fase
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x="step", y="tempForno_future")
plt.title("Distribuzione temperatura futura per fase")
plt.grid(True)
plt.show()

#boxplot output
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x="step", y="resOutput")
plt.title("Distribuzione potenza applicata per fase")
plt.grid(True)
plt.show()

#boxplot deltaT
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x="step", y="deltaT_future")
plt.title("Distribuzione deltaT futura per fase")
plt.grid(True)
plt.show()


#VIOLIN PLOT
plt.figure(figsize=(10, 6))
sns.violinplot(data=df, x="step", y="tempForno", inner="quartile")
plt.title("Distribuzione (violin) temperatura per fase")
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
sns.violinplot(data=df, x="step", y="resOutput", inner="quartile")
plt.title("Distribuzione (violin) potenza per fase")
plt.grid(True)
plt.show()

plt.figure(figsize=(10, 6))
sns.violinplot(data=df, x="step", y="deltaT_future", inner="quartile")
plt.title("Distribuzione (violin) deltaT per fase")
plt.grid(True)
plt.show()