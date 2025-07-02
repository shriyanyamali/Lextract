count = 0

# Open the file with utf-8 encoding
with open("", "r", encoding="utf-8") as file:  # Specify the path to your file
    for line in file:    
        words = line.split(" ")
        count += len(words)

print("Number of words present in given file: " + str(count))
