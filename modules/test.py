import pandas as pd
df = pd.DataFrame({"frame_index": [1,2,3,4,1,2]})
print(df)
sequence = [2,5]
df.loc[df["frame_index"] == 2, "sequence_number"] = sequence
df.ffill(inplace=True)  # alias for df.fillna(method="ffill")

print(df)