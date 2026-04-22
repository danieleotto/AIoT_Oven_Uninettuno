import sys, time
from max6675lib import MAX6675, MovingAverage
from logger import fileLogger
from ssrelay import SSR

PIN_SCK = 8
PIN_CS = 7
PIN_DO = 5
PIN_SSR_RES = 2

x_time = []
y_temp = []

tc = MAX6675(PIN_SCK, PIN_CS, PIN_DO)
ma = MovingAverage(int(input("Inserire numero di campioni per ogni lettura: ")))
lg = fileLogger(input("Inserire nome file per il log completo di estensione: "))
ssr_res = SSR(PIN_SSR_RES)

target = float(input("Inserire temperatura target: "))
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

        if counter >= ma.size:
            elapsed_time = time.time() - start_time
            avg = ma.average()
            if avg < target:
                ssr_res.HIGH()
            else:
                ssr_res.LOW()
            x_time.append(elapsed_time)
            y_temp.append(avg)
            sys.stdout.write(f"\rTemperatura media ultimi {ma.size} campioni: {avg:.2f} °C | Tempo: {elapsed_time:.2f} s | SSR On: {ssr_res.isOn} |Numero campione: {n_camp}")
            lg.log(avg,elapsed_time,ssr_res.isOn,n_camp)
            counter = 0
            n_camp += 1


except KeyboardInterrupt:
    print("\nExit")
    for i in range(0, len(x_time)):
        print(f"Temperatura media: {y_temp[i]:.2f} °C | Tempo: {x_time[i]:.2f} s | Numero campione: {i+1}")


