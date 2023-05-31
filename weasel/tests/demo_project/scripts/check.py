import pathlib

workdir = pathlib.Path(__file__).parent.resolve().parent

text = """
                             _
__      _____  __ _ ___  ___| |
\\ \\ /\\ / / _ \\/ _` / __|/ _ \\ |
 \\ V  V /  __/ (_| \\__ \\  __/ |
  \\_/\\_/ \\___|\\__,_|___/\\___|_|

"""

with open(workdir / "corpus/stuff.txt", "w") as outfile:
    outfile.write(text)
