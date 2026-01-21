

import requests



marketId = "93"
response = requests.get(
    f"https://openapi.opinion.trade/openapi/market/categorical/{marketId}",
    headers={"apikey":"ywpg2k79OPO3w39KrRX7dz5zRhB736Cg","Accept":"*/*"},
)

data = response.json()
print(data)