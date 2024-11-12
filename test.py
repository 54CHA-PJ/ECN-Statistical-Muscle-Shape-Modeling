for i in range(1, 101):
    res = ''
    if i%3 == 0:
        res += "Fizz "
    if i%5 == 0:
        res += "Buzz"
    print(res if res!= '' else i)