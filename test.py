import requests

# localhost -> comp ip
# 8000 -> port
# /users -> endpoint (route)
# ?id=1 -> argument

# create_product_res = requests.post("http://localhost:8000/users", 
#                          params={"username": "Chpl", "password" : "gago2000"})

# print("create->", create_product_res.json())

# get_products_res = requests.get("http://localhost:8000/users?id=2")

# print("read->", get_products_res.text)

# update_product_res = requests.put("http://localhost:8000/users", 
#                                      params={"id": "2", "username": "Chlp"})

# print("update->", update_product_res.text)

delete_product_res = requests.delete("http://localhost:8000/users", 
                                     params={"id": "2"})

print("update->", delete_product_res.text)