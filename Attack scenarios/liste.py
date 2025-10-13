with open("seid_to_delete.txt") as f:
    liste = [int(line.strip(), 16) for line in f]
                 # affiche en décimal
#print([hex(x) for x in liste])  # affiche en hexa, mais avec quotes
print("[" + ", ".join(f"0x{val:x}" for val in liste) + "]")

