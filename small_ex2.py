import dill

s = 'This is a string!  How nice?'
print(f'Original string: {s}')
with open('tst.txt', 'wb') as f:
    f.write(dill.dumps(s))

with open('tst.txt', 'rb') as f:
    s = dill.loads(f.read())

print(s)