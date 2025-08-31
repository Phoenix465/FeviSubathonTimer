from time import sleep
import obsws_python as obs

# pass conn info if not in config.toml
cl = obs.ReqClient(host='localhost', port=4455, password='cTSydoJdOA7zNhz0', timeout=3)
resp = cl.get_version()

print(f"OBS Version: {resp.obs_version}")


i = 0
while True:
    sleep(5)
    i += 1
    cl.disconnect()
    # cl.set_input_settings("FeviSubathonTimer-Points", {"text": str(i)}, True)
    # cl.set_input_settings("FeviSubathonTimer-Timer", {"text": f"00:00:{i}"}, True)

# obsws_python.error.OBSSDKRequestError: Request SetInputSettings returned code 600. With message: No source was found by the name of `FeviSubathonTimer-Points11`.
# json.decode
