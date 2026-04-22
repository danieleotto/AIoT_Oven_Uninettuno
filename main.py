import sys, time
from max6675lib import MAX6675

P_SCK = 8
P_CS = 7
P_DO = 5

tc = MAX6675(P_SCK, P_CS, P_DO)

try:
    print("Press CTRL+C to exit")
    start_time = time.time()
    while True:
        temp = tc.readTempC()
        elapsed_time = time.time() - start_time
        if temp is None:
            sys.stdout.write(f"\rTermocoppia non collegata.")
        else:
            sys.stdout.write(f"\rTemperatura: {temp:.2f} °C | Tempo: {elapsed_time:.2f} s")
        sys.stdout.flush()
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exit")


