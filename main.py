import sys, time
from max6675lib import MAX6675, MovingAverage
from logger import fileLogger

P_SCK = 8
P_CS = 7
P_DO = 5

tc = MAX6675(P_SCK, P_CS, P_DO)

x_time = []
y_temp = []

lg = fileLogger(input("Inserire nome file per il log completo di estensione: "))
ws = int(input("Inserire numero di campioni per ogni lettura: "))
ma = MovingAverage(ws)
counter = 0
n_camp = 1

try:
    print("Press CTRL+C to exit")
    start_time = time.time()
    while True:
        temp = tc.readTempC()
        if temp is not None:
            ma.add(temp)
        else:
            sys.stdout.write(f"\rTermocoppia non collegata.")
        time.sleep(0.2)
        counter += 1

        if counter >= ws:
            elapsed_time = time.time() - start_time
            avg = ma.average()
            x_time.append(elapsed_time)
            y_temp.append(avg)
            sys.stdout.write(f"\rTemperatura media ultimi {ws} campioni: {avg:.2f} °C | Tempo: {elapsed_time:.2f} s | Numero campione: {n_camp}")
            lg.log(avg,elapsed_time,n_camp)
            counter = 0
            n_camp += 1


except KeyboardInterrupt:
    print("\nExit")
    for i in range(0, len(x_time)):
        print(f"Temperatura media: {y_temp[i]:.2f} °C | Tempo: {x_time[i]:.2f} s | Numero campione: {i+1}")


