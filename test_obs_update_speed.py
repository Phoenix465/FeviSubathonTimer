from time import sleep
import obsws_python as obs

# pass conn info if not in config.toml
cl = obs.ReqClient(host='localhost', port=4455, password='cTSydoJdOA7zNhz0', timeout=3)
resp = cl.get_version()
print(f"OBS Version: {resp.obs_version}")


i = 0
while True:
    sleep(0.05)
    i += 1
    cl.set_input_settings("FeviSubathonTimer-Points", {"text": str(i)}, True)
    cl.set_input_settings("FeviSubathonTimer-Timer", {"text": f"00:00:{i}"}, True)

