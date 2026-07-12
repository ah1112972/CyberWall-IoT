#lists
mov1= input("Enter 1st movie: ")
mov2= input("Enter 2nd movie: ")
mov3= input("Enter 3rd movie: ")

Movies = [mov1, mov2, mov3]
print(Movies)
Movies.append("GOT")
print(Movies)
print(Movies.count("GOT"))

Movies.insert(1, "spiderman")
print(Movies)

Movies.sort()
print(Movies)

print(type(Movies))

print("=" * 50)

#Palindrom
List1 = [1 ,"apple", 2, "apple", 1]
List2 = [1,2,3,4]

CopyL1 = List1.copy()
CopyL1.reverse()

CopyL2 = List2.copy()
CopyL2.reverse()

if List1 == CopyL1:
    print("Palindrome ")
else:
    print("Not Palindrome")

if List2 == CopyL2:
    print("Palindrome ")
else:
    print("Not Palindrome")    



