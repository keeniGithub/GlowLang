from src.run.run import run

while True:
    text = input("GlowShell >>> ")
    result, error = run("<stdin>", text)

    if error: print(error.as_string())
    elif result: print(result)