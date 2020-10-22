import pickle


with open("facts.txt") as file:
    text = file.read()
    lines = text.split("\n\n")

with open("facts.pkl", 'wb') as file:
    pickle.dump(lines, file)
