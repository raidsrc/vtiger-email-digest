import pandas as pd

file = pd.read_csv('Projects_2026-02-25_1624.csv')
goisizekb = file["GOI Size (kb)"]
decimal = round(goisizekb / 1000, 2)
file["GOI Size (kb)"] = decimal
print(decimal)
file.to_csv('csv.csv', index=False)