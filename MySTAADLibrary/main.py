from mystaad import OpenSTAAD
staad = OpenSTAAD()
last_node = staad.geometry.GetLastNodeNo()
print(last_node)