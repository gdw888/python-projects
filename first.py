print("\n")


text = "'This is my first hello world'"
print(text)
text = '"This is my first hello world"'
print(text)


text = "123"
print(type(text))

text= "This is how to escape a special \"character\"."
print((text))

text= r"This is an alternative way to escape a special \"character\"."
print((text))

text = ("""\nmultiple lines1
multiple lines2
multiple lines3""")

print((text))

text *= 3
print((text))


text = ('hello'
        "world")
print((text))

text = text + " welcome"
print((text))

print(text[0])
print(text[1:3])


print(text[-20:])
#print(text[-20]) index error


text= "hello world"
print(len(text))


text= "my "+text[6:1000]
print((text))



list = [1,2,3,"helloworld"]

print(list)

list, list2= [1,2,3,"helloworld",list],list

print(list)
print(list2)

x = 0

if x < 0:
    print("Negative")
elif x > 0:
    print("positive")
else:
    print("zero")


list = ["1,2,3,,]","helloworld"]

for element in list:
    print(str(element))
    print( len(element))

print("\n\n")
for n in range(2, 10):
    for x in range(2, n):
        if n % x == 0:
            print(n, 'equals', x, '*', n//x)
            break
    else:
        # loop fell through without finding a factor
        print(n, 'is a prime number', x)












